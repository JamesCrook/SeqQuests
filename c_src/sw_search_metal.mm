#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>
#include <sys/stat.h>
#include <chrono>

#define NS_PRIVATE_IMPLEMENTATION
#define CA_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION

#include <Foundation/Foundation.hpp>
#include <Metal/Metal.hpp>
#include <QuartzCore/QuartzCore.hpp>

#define MAX_DESCRIPTION_LEN 256
#ifndef THREADS
#define THREADS (4096)
#endif

#ifndef UNROLL
#define UNROLL (32)
#endif

/*
# Metal SW Searcher

`sw_search_metal.mm` is a command-line tool that performs a Smith-Waterman (SW) local sequence alignment search. It is written in Objective-C and utilizes Apple's Metal framework to GPU accelerate search.

## Core Functionality

The tool takes a query protein sequence and searches for local alignments against a database of protein sequences in FASTA format. It operates directly on pre-compiled binary data, avoiding the overhead of parsing text files at runtime. The binary data is prepared using script `prepare_data.py`

## PAM Look-Up Table (LUT)

For each search, the tool pre-computes a look-up table (LUT) for the query sequence based on the PAM substitution matrix. This `pam_lut` is a `int16` array with a size 32 times that of the query sequence. This lut removes one step of indirect access from the alignment calculation.

The actual amino acid alphabet in the PAM substitution matrix is 26. 32 is the next largest power of 2. The characater '@' is used for end of sequence, and has a penalty of 30,000 for matching anything. This is part of resetting the scores at the end of sequences without doing branching.

## Parallel Execution

The search of one query sequence is against a database of sequences. The workload is divided as follows:

-   **THREADS:** This compile-time constant, usually 4096, defines how many database sequences are processed in parallel by the GPU. Each sequence is assigned to a separate thread.
-   **UNROLL:** This constant, usually 40, determines how many elements of a database sequence are processed by a single GPU thread in one go. Each of the THREADS threads is working on a grid of size query sequence size x UNROLL. All threads work on the same sized blocks of data. These blocks of calculation are using in thread memory, and reading and writing cache only for the boundary data. 

## Kernel Output

The Metal kernel executes the SW algorithm and, for each database sequence, it returns an array of scores, each thread returning batches of size UNROLL. These scores are the **maximum local alignment score ending at each residue** in the database sequence. Additionally the threads do a running max for sequences in the UNROLLed block, to get the overall max score for each sequence.
*/


typedef struct {
    int32_t description_len;
    char* description;
    int32_t sequence_len;
    char* sequence;
} FastaRecord;

typedef struct {
    int debug_slot;
    int reporting_threshold;
    int start_at;
    int num_seqs;
    bool machine_output;
    bool slow_output;
    const char* pam_data_file;
    const char* fasta_data_file;
} AppSettings;

typedef struct {
    MTL::Device* device;
    MTL::Library* library;
    MTL::ComputePipelineState* pipeline;
    MTL::CommandQueue* queue;
    MTL::Buffer* data_buffers[2];
    MTL::Buffer* pam_buffer;
    MTL::Buffer* aa_buffer;
    MTL::Buffer* max_buffer;
    MTL::Buffer* rows_buffer;
} MetalState;

typedef struct {
    int16_t pam_data[32 * 32];
    FastaRecord* fasta_records;
    int num_fasta_records;
} DataManager;

// --- Function Prototypes ---
void parse_arguments(int argc, char* argv[], AppSettings* settings);
bool setup_metal(MetalState* metal_state);
bool load_all_data(const AppSettings* settings, DataManager* data_manager);
bool prepare_for_sequence(MetalState* metal_state, const DataManager* data_manager, int probe_seq_idx);
void run_search(int query, MetalState* metal_state, const DataManager* data_manager, const AppSettings* settings, int rows);
void report_results(int rows, int steps, int finds, std::chrono::duration<double> elapsed);
void cleanup(MetalState* metal_state, DataManager* data_manager);
long file_size(const char* filename);
void load_pam_data(const char* filename, int16_t* pam_data);
FastaRecord* load_fasta_data(const char* filename, int* num_records);
void release_fasta_records(FastaRecord* records, int num_records);

// --- Main ---
int main(int argc, char * argv[]) {
    @autoreleasepool {
        AppSettings settings;
        parse_arguments(argc, argv, &settings);

        DataManager data_manager;
        if (!load_all_data(&settings, &data_manager)) {
            return 1;
        }

        MetalState metal_state;
        if (!setup_metal(&metal_state)) {
            return 1;
        }

        for (int i = 0; i < settings.num_seqs; ++i) {
            int probe_seq_idx = settings.start_at + i;
            if (probe_seq_idx >= data_manager.num_fasta_records) {
                printf("No more sequences to process.\n");
                break;
            }

            if (!prepare_for_sequence(&metal_state, &data_manager, probe_seq_idx)) {
                continue; // Skip to next sequence
            }

            int rows = data_manager.fasta_records[probe_seq_idx].sequence_len;
            run_search(probe_seq_idx, &metal_state, &data_manager, &settings, rows);

            // Release sequence-specific buffers
            metal_state.pam_buffer->release();
            metal_state.rows_buffer->release();
            metal_state.data_buffers[0]->release();
            metal_state.data_buffers[1]->release();
        }

        cleanup(&metal_state, &data_manager);
    }
    return 0;
}

void parse_arguments(int argc, char* argv[], AppSettings* settings) {
    settings->debug_slot = -10;
    settings->reporting_threshold = 110;
    settings->start_at = 0;
    settings->num_seqs = 1;
    settings->machine_output = true;
    settings->slow_output = false;
    settings->pam_data_file = "c_src/pam250.bin";
    settings->fasta_data_file = "c_src/fasta.bin";

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--debug_slot") == 0 && i + 1 < argc) {
            settings->debug_slot = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--reporting_threshold") == 0 && i + 1 < argc) {
            settings->reporting_threshold = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--start_at") == 0 && i + 1 < argc) {
            settings->start_at = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--num_seqs") == 0 && i + 1 < argc) {
            settings->num_seqs = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--slow_output") == 0) {
            settings->slow_output = true;
        } else if (strcmp(argv[i], "--machine_output") == 0) {
            settings->machine_output = true;
        } else if (strcmp(argv[i], "--pam_data") == 0 && i + 1 < argc) {
            settings->pam_data_file = argv[++i];
        } else if (strcmp(argv[i], "--fasta_data") == 0 && i + 1 < argc) {
            settings->fasta_data_file = argv[++i];
        }
    }
}

bool setup_metal(MetalState* metal_state) {
    metal_state->device = MTL::CreateSystemDefaultDevice();
    if (!metal_state->device) {
        fprintf(stderr, "Metal is not supported on this device.\n");
        return false;
    }
    printf("Device: %s\n", metal_state->device->name()->utf8String());

    NS::Error* error = nullptr;
    NS::String* library_path = NS::String::string("bin/sw.metallib", NS::UTF8StringEncoding);
    metal_state->library = metal_state->device->newLibrary(library_path, &error);
    if (!metal_state->library) {
        fprintf(stderr, "Failed to create library: %s\n", error->localizedDescription()->utf8String());
        return false;
    }

    MTL::Function* kernel_function = metal_state->library->newFunction(NS::String::string("sw_step", NS::UTF8StringEncoding));
    metal_state->pipeline = metal_state->device->newComputePipelineState(kernel_function, &error);
    if (!metal_state->pipeline) {
        fprintf(stderr, "Failed to create pipeline state: %s\n", error->localizedDescription()->utf8String());
        return false;
    }

    metal_state->queue = metal_state->device->newCommandQueue();

    metal_state->aa_buffer = metal_state->device->newBuffer(UNROLL * THREADS * sizeof(int16_t), MTL::ResourceStorageModeShared);
    metal_state->max_buffer = metal_state->device->newBuffer(UNROLL * THREADS * 2 * sizeof(int16_t), MTL::ResourceStorageModeShared);

    kernel_function->release();
    return true;
}

bool load_all_data(const AppSettings* settings, DataManager* data_manager) {
    load_pam_data(settings->pam_data_file, data_manager->pam_data);
    data_manager->fasta_records = load_fasta_data(settings->fasta_data_file, &data_manager->num_fasta_records);
    return data_manager->fasta_records != NULL;
}

bool prepare_for_sequence(MetalState* metal_state, const DataManager* data_manager, int probe_seq_idx) {
    char* search_sequence = data_manager->fasta_records[probe_seq_idx].sequence;
    // -1 because of the terminating @
    int rows = data_manager->fasta_records[probe_seq_idx].sequence_len-1;

    printf("\nSearching with: %s\n", data_manager->fasta_records[probe_seq_idx].description);
    printf("Sequence: %6d Sequence length: %6d\n", probe_seq_idx, rows);

    int16_t* pam_lut = (int16_t*)malloc(32 * rows * sizeof(int16_t));
    for (int col = 0; col < 32; ++col) {
        for (int i = 0; i < rows; ++i) {
            int aa_idx = (int)search_sequence[i] & 31;
            pam_lut[col * rows + i] = data_manager->pam_data[col * 32 + aa_idx];
        }
    }

    metal_state->data_buffers[0] = metal_state->device->newBuffer(THREADS * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
    metal_state->data_buffers[1] = metal_state->device->newBuffer(THREADS * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
    memset(metal_state->data_buffers[0]->contents(), 0, THREADS * rows * sizeof(int16_t));
    memset(metal_state->data_buffers[1]->contents(), 0, THREADS * rows * sizeof(int16_t));

    metal_state->pam_buffer = metal_state->device->newBuffer(pam_lut, 32 * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
    free(pam_lut);

    uint32_t num_rows_val = rows;
    metal_state->rows_buffer = metal_state->device->newBuffer(&num_rows_val, sizeof(uint32_t), MTL::ResourceStorageModeShared);

    //printf("Matrix: %dx%d\n", THREADS, rows);
    //printf("Buffers created\n");
    return true;
}

void run_search(int query, MetalState* metal_state, const DataManager* data_manager, const AppSettings* settings, int rows) {
    printf("\nRunning Smith-Waterman steps...\n");
    auto start = std::chrono::high_resolution_clock::now();

    int16_t* aa_data = (int16_t*)metal_state->aa_buffer->contents();
    int16_t* final_max = (int16_t*)metal_state->max_buffer->contents();
    memset(final_max, 0, THREADS * 2 * UNROLL * sizeof(int16_t));

    int pos[THREADS] = {0};
    int pos_reported[THREADS] = {0};
    int seqno[THREADS], seqno_to_report[THREADS], first_hit[THREADS], last_hit[THREADS];
    for(int i=0; i<THREADS; ++i) seqno[i] = seqno_to_report[i] = first_hit[i] = last_hit[i] = -1;

    int seq = -1;
    bool more_data = true;
    bool do_search = true;
    int step = -1;
    int finds = 0;

    int seqChar = 0;
    while(more_data) {
        @autoreleasepool {        
            step++;
            more_data = false;


            for (int i = 0; i < THREADS; ++i) {
                for (int j = 0; j < UNROLL; j++){
                    if(seqno[i] == -2) continue;

                    bool seqDone = (seqno[i] == -1 || pos[i] >= data_manager->fasta_records[seqno[i]].sequence_len);
                    if(seqDone) {
                        seq++;
                        while (seq < data_manager->num_fasta_records && data_manager->fasta_records[seq].sequence_len < (UNROLL+4)) {
                            seq++;
                        }
                        if (seq < data_manager->num_fasta_records) {
                            pos[i] = 0;
                            seqno[i] = seq;
                            if( seqno_to_report[i]==-1)
                                seqno_to_report[i] = seq;
                        } else {
                            seqno[i] = -2;
                            continue;
                        }
                    }
                    aa_data[i*UNROLL+j] = data_manager->fasta_records[seqno[i]].sequence[pos[i]] & 31;
                    pos[i]++;
                    more_data = true;
                }
            }

            if(!more_data) break;
            if((step % 1000) == 0) printf("Step:%7d\n", step);

            int in_idx = step % 2;
            int out_idx = (step + 1) % 2;

            if( do_search ){
                MTL::CommandBuffer* command_buffer = metal_state->queue->commandBuffer();
                MTL::ComputeCommandEncoder* encoder = command_buffer->computeCommandEncoder();
                encoder->setComputePipelineState(metal_state->pipeline);
                encoder->setBuffer(metal_state->data_buffers[in_idx], 0, 0);
                encoder->setBuffer(metal_state->data_buffers[out_idx], 0, 1);
                encoder->setBuffer(metal_state->pam_buffer, 0, 2);
                encoder->setBuffer(metal_state->aa_buffer, 0, 3);
                encoder->setBuffer(metal_state->max_buffer, 0, 4);
                encoder->setBuffer(metal_state->rows_buffer, 0, 5);

                MTL::Size grid_size = MTL::Size(THREADS, 1, 1);
                NS::UInteger threadgroup_size_val = metal_state->pipeline->maxTotalThreadsPerThreadgroup();
                if (threadgroup_size_val > THREADS) threadgroup_size_val = THREADS;
                MTL::Size threadgroup_size = MTL::Size(threadgroup_size_val, 1, 1);

                encoder->dispatchThreads(grid_size, threadgroup_size);
                encoder->endEncoding();
                command_buffer->commit();
                command_buffer->waitUntilCompleted();
            }

            for (int i = 0; i < THREADS; ++i) {

                //if(seqno_to_report[i] == -1) seqno_to_report[i] = seqno[i];


                for (int j = 0; j < UNROLL; j++){
                    if(seqno_to_report[i] == -2) continue;
                    if(seqno_to_report[i] == settings->debug_slot) {
                        int16_t scoret1 = final_max[(i * UNROLL +j) * 2 ];
                        int16_t scoret2 = final_max[(i * UNROLL +j) * 2 + 1];
                        char aminoAcid = '@'+aa_data[i*UNROLL+j];
                        printf( "Seq:%d %c i:%d j:%d t1:%d t2:%d\n",seqno_to_report[i], aminoAcid, seqChar, j, scoret1, scoret2);
                        seqChar++;
                        // ... debug output ...
                    }

                    // score here is max for this column...
                    int16_t score = final_max[(i * UNROLL +j) * 2];
                    if( score >= settings->reporting_threshold ){
                        if( first_hit[i] < 0)
                            first_hit[i] = pos_reported[i];
                        last_hit[i] = pos_reported[i];
                    }
                    pos_reported[i] += 1;
                    if( aa_data[i*UNROLL+j] == 0 ){
                        // score here is the max for the protein...
                        score = final_max[(i * UNROLL +j) * 2 + 1];
                        if (score >= settings->reporting_threshold) {
                            if( settings->machine_output ){
                                printf("HIT:%d,%d,%d,%d,%d\n", query, seqno_to_report[i], score, first_hit[i],last_hit[i]-first_hit[i] );
                            }
                            else {
                                printf("Step:%7d Seq:%6d Length:%5d Score:%6d Name:%.100s\n",
                                    step, seqno_to_report[i], data_manager->fasta_records[seqno_to_report[i]].sequence_len - 1, score, data_manager->fasta_records[seqno_to_report[i]].description);
                            }
                            if(settings->slow_output) usleep(100000);
                            finds++;
                        }
                        final_max[(i * UNROLL +j)* 2 + 1] = 0;
                        if( seqno_to_report[i] == seqno[i] )
                            seqno_to_report[i] = -1;
                        else
                            seqno_to_report[i] = seqno[i];
                        pos_reported[i] = 0;
                        first_hit[i] = -1;
                        last_hit[i] = -1;// not actually required.
                    }
                }
            }
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    report_results(rows, step, finds, end - start);
}

void report_results(int rows, int steps, int finds, std::chrono::duration<double> elapsed) {
    printf("Step:%7d <-- Finished\n", steps);
    printf("Searched with %4daa protein vs %8daa database; %4d finds\n", rows, steps * THREADS * UNROLL, finds);
    printf("Execution time: %.4f seconds\n", elapsed.count());
}

void cleanup(MetalState* metal_state, DataManager* data_manager) {
    release_fasta_records(data_manager->fasta_records, data_manager->num_fasta_records);
    metal_state->aa_buffer->release();
    metal_state->max_buffer->release();
    metal_state->queue->release();
    metal_state->pipeline->release();
    metal_state->library->release();
    metal_state->device->release();
}

// --- Helper Functions ---

long file_size(const char* filename) {
    struct stat st;
    if (stat(filename, &st) == 0)
        return st.st_size;
    return -1;
}

void load_pam_data(const char* filename, int16_t* pam_data) {
    FILE* f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error opening %s\n", filename);
        exit(1);
    }
    fread(pam_data, sizeof(int16_t), 32 * 32, f);
    fclose(f);
    printf("PAM data loaded from %s\n", filename);
}

FastaRecord* load_fasta_data(const char* filename, int* num_records) {
    FILE* f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error opening %s\n", filename);
        return NULL;
    }

    int capacity = 1000;
    FastaRecord* records = (FastaRecord*)malloc(sizeof(FastaRecord) * capacity);
    int count = 0;

    int32_t description_len;
    while (fread(&description_len, sizeof(int32_t), 1, f) == 1) {
        if (count >= capacity) {
            capacity *= 2;
            records = (FastaRecord*)realloc(records, sizeof(FastaRecord) * capacity);
        }
        records[count].description_len = description_len;
        records[count].description = (char*)malloc(records[count].description_len + 1);
        fread(records[count].description, 1, records[count].description_len, f);
        records[count].description[records[count].description_len] = '\0';

        fread(&records[count].sequence_len, sizeof(int32_t), 1, f);
        records[count].sequence = (char*)malloc(records[count].sequence_len + 1);
        fread(records[count].sequence, 1, records[count].sequence_len, f);
        records[count].sequence[records[count].sequence_len] = '\0';

        count++;
    }

    *num_records = count;
    printf("Loaded %d sequences from %s\n", count, filename);
    fclose(f);
    return records;
}

void release_fasta_records(FastaRecord* records, int num_records) {
    for (int i = 0; i < num_records; ++i) {
        free(records[i].description);
        free(records[i].sequence);
    }
    free(records);
}
