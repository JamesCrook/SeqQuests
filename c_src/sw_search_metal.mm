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
#define UNROLL (40)
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
    bool all_recs;
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

typedef struct {
    std::chrono::time_point<std::chrono::high_resolution_clock> global_start_time;
    
    // Cumulative counters
    int64_t total_comparisons_computed;
    int64_t total_pmes_computed;
    int64_t total_pmes_wasted;
    double total_gpu_time;
    double total_cpu_time;
    
    // Database statistics (computed once at startup)
    int non_skipped_proteins;
    int64_t non_skipped_amino_acids;
    double average_protein_length;
    int64_t task_protein_comparisons;
    int64_t task_pmes;
    int64_t total_all_on_all_comparisons;
    int64_t total_all_on_all_pmes;
} BenchmarkState;

// --- Function Prototypes ---
void parse_arguments(int argc, char* argv[], AppSettings* settings);
bool setup_metal(MetalState* metal_state);
bool load_all_data(const AppSettings* settings, DataManager* data_manager);
bool prepare_for_sequence(MetalState* metal_state, const DataManager* data_manager, int probe_seq_idx);
void run_search(int query, MetalState* metal_state, const DataManager* data_manager, const AppSettings* settings, int rows, BenchmarkState* bench);
void report_results(int rows, int steps, int finds, std::chrono::duration<double> elapsed, 
                   int query_seq, const AppSettings* settings, const DataManager* data_manager, 
                   BenchmarkState* bench);
void cleanup(MetalState* metal_state, DataManager* data_manager);
long file_size(const char* filename);
void load_pam_data(const char* filename, int16_t* pam_data);
FastaRecord* load_fasta_data(const char* filename, int* num_records);
void release_fasta_records(FastaRecord* records, int num_records);
bool skip_sequence(const DataManager* data_manager, int query, int seq, const AppSettings* settings);
void initialize_benchmark(BenchmarkState* bench, const DataManager* data_manager, const AppSettings* settings);
void format_time(double seconds, char* buffer, size_t buffer_size);
void format_number_with_commas(int64_t number, char* buffer, size_t buffer_size);

// --- Main ---
int main(int argc, char * argv[]) {
    printf( "compiled with THREADS:%i UNROLL:%i\n", THREADS, UNROLL);
    @autoreleasepool {
        AppSettings settings;
        parse_arguments(argc, argv, &settings);

        DataManager data_manager;
        if (!load_all_data(&settings, &data_manager)) {
            return 1;
        }

        BenchmarkState bench;
        initialize_benchmark(&bench, &data_manager, &settings);

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
            run_search(probe_seq_idx, &metal_state, &data_manager, &settings, rows, &bench);

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
    settings->all_recs = false;
    settings->machine_output = true;
    settings->slow_output = false;
    settings->pam_data_file = "data/pam250.bin";
    settings->fasta_data_file = "data/fasta.bin";

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--debug_slot") == 0 && i + 1 < argc) {
            settings->debug_slot = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--reporting_threshold") == 0 && i + 1 < argc) {
            settings->reporting_threshold = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--start_at") == 0 && i + 1 < argc) {
            settings->start_at = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--num_seqs") == 0 && i + 1 < argc) {
            settings->num_seqs = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--all_recs") == 0) {
            settings->all_recs = true;
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
    printf("SEQ: %6d Sequence length: %6d\n", probe_seq_idx, rows);
    printf("STATS: Sequence: %6d Step: 0\n", probe_seq_idx);

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

// True if we should skip this sequence
bool skip_sequence( const DataManager* data_manager, int query, int seq, const AppSettings* settings ){
    if( seq >= data_manager->num_fasta_records)
        return false;
    //if( data_manager->fasta_records[seq].sequence_len > 8000)
    //    return true;
    //if( data_manager->fasta_records[seq].sequence_len < (UNROLL+4))
    //    return true;
    if( settings->all_recs)
        return false;
    return seq < query;
}

void initialize_benchmark(BenchmarkState* bench, const DataManager* data_manager, const AppSettings* settings) {
    bench->global_start_time = std::chrono::high_resolution_clock::now();
    bench->total_comparisons_computed = 0;
    bench->total_pmes_computed = 0;
    bench->total_pmes_wasted = 0;
    bench->total_gpu_time = 0.0;
    bench->total_cpu_time = 0.0;
    
    // Calculate non-skipped proteins and amino acids
    // Use query==0 so seq < query is always false, getting full database stats
    bench->non_skipped_proteins = 0;
    bench->non_skipped_amino_acids = 0;
    
    for (int i = 0; i < data_manager->num_fasta_records; i++) {
        if (!skip_sequence(data_manager, 0, i, settings)) {
            bench->non_skipped_proteins++;
            bench->non_skipped_amino_acids += data_manager->fasta_records[i].sequence_len;
        }
    }

    bench->task_protein_comparisons = 0;
    bench->task_pmes = 0;

    int last_protein = settings->start_at + settings->num_seqs -1;
    if( last_protein >= data_manager->num_fasta_records )
        last_protein = data_manager->num_fasta_records-1;

    int64_t proteins_left = data_manager->num_fasta_records - settings->start_at;
    int64_t amino_acids_left = bench->non_skipped_amino_acids;
    bool isTriangular = true;
    for (int i = settings->start_at; i <= last_protein ; i++) {
        if (!skip_sequence(data_manager, 0, i, settings)) {
            int64_t this_seq_size = data_manager->fasta_records[i].sequence_len;
            if( isTriangular ){
                // Diminishing work
                bench->task_protein_comparisons += proteins_left;
                bench->task_pmes += this_seq_size * amino_acids_left;
            } else { 
                // Constant work
                bench->task_protein_comparisons += bench->non_skipped_proteins++;
                bench->task_pmes += this_seq_size * bench->non_skipped_amino_acids;
            }
            amino_acids_left -= this_seq_size;
        }
        proteins_left--;
    }

    
    bench->average_protein_length = (double)bench->non_skipped_amino_acids / bench->non_skipped_proteins;
    
    // All-on-all estimates (always triangular)
    bench->total_all_on_all_comparisons = (int64_t)bench->non_skipped_proteins * (bench->non_skipped_proteins - 1) / 2;
    bench->total_all_on_all_pmes = bench->non_skipped_amino_acids * bench->non_skipped_amino_acids / 2;


    
    printf("BENCH: \nBENCH: === Database Statistics ===\n");
    printf("BENCH: Total proteins: %d\n", data_manager->num_fasta_records);
    printf("BENCH: Non-skipped proteins: %d\n", bench->non_skipped_proteins);
    printf("BENCH: Total amino acids: %lld\n", bench->non_skipped_amino_acids);
    printf("BENCH: Average protein length: %.1f\n", bench->average_protein_length);
    printf("All-on-all comparisons (triangular): %lld\n", bench->total_all_on_all_comparisons);
    printf("BENCH: All-on-all PMEs: %lld\n", bench->total_all_on_all_pmes);
    printf("BENCH: Task comparisons: %lld\n", bench->task_protein_comparisons);
    printf("BENCH: Task PMEs: %lld\n", bench->task_pmes);
    printf("BENCH: \n");
}

void format_time(double seconds, char* buffer, size_t buffer_size) {
    int days = (int)(seconds / 86400);
    seconds -= days * 86400;
    int hours = (int)(seconds / 3600);
    seconds -= hours * 3600;
    int mins = (int)(seconds / 60);
    seconds -= mins * 60;
    
    snprintf(buffer, buffer_size, "%dd %dh %dm %.0fs", days, hours, mins, seconds);
}

void format_number_with_commas(int64_t number, char* buffer, size_t buffer_size) {
    char temp[64];
    snprintf(temp, sizeof(temp), "%ld", (long)number);
    
    int len = strlen(temp);
    int comma_count = (len - 1) / 3;
    int total_len = len + comma_count;
    
    if (total_len >= (int)buffer_size) {
        snprintf(buffer, buffer_size, "%ld", (long)number);
        return;
    }
    
    int src_pos = len - 1;
    int dst_pos = total_len - 1;
    buffer[dst_pos + 1] = '\0';
    
    int digit_count = 0;
    while (src_pos >= 0) {
        buffer[dst_pos--] = temp[src_pos--];
        digit_count++;
        if (digit_count == 3 && src_pos >= 0) {
            buffer[dst_pos--] = ',';
            digit_count = 0;
        }
    }
}


void run_search(int query, MetalState* metal_state, const DataManager* data_manager, const AppSettings* settings, int rows, BenchmarkState* bench) {
    printf("\nRunning Smith-Waterman steps...\n");
    auto search_start = std::chrono::high_resolution_clock::now();
    auto cpu_start = search_start;

    int16_t* aa_data = (int16_t*)metal_state->aa_buffer->contents();
    int16_t* final_max = (int16_t*)metal_state->max_buffer->contents();
    memset(final_max, 0, THREADS * 2 * UNROLL * sizeof(int16_t));

    int pos[THREADS] = {0};
    int pos_reported[THREADS] = {0};
    int seqno[THREADS], first_hit[THREADS], last_hit[THREADS];
    for(int i=0; i<THREADS; ++i) seqno[i] = first_hit[i] = last_hit[i] = -1;

    int seq_queue[THREADS][UNROLL + 1]; 
    int q_head[THREADS] = {0}; 
    int q_tail[THREADS] = {0};
    int current_report_seq = -1; 

    int seq = -1;
    if( !settings->all_recs)
        seq = query-1;
    bool more_data = true;
    bool do_search = true;
    int step = -1;
    int finds = 0;
    
    int comparisons_this_search = 0;
    int64_t pmes_this_search = 0;
    int64_t wasted_pmes_this_search = 0;
    double gpu_time_this_search = 0.0;

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
                        while (skip_sequence( data_manager, query, seq, settings )) {
                            seq++;
                        }
                        if (seq < data_manager->num_fasta_records) {
                            pos[i] = 0;
                            seqno[i] = seq;
                            seq_queue[i][q_tail[i]] = seq; // Write to current tail
                            q_tail[i] = (q_tail[i] + 1) % (UNROLL + 1); // Wrap carefully                            
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
            if((step % 1000) == 0) printf("STATS: Sequence: %6d Step:%7d\n", query, step);

            int in_idx = step % 2;
            int out_idx = (step + 1) % 2;

            // Track CPU time up to this point
            auto cpu_end = std::chrono::high_resolution_clock::now();
            double cpu_time_delta = std::chrono::duration<double>(cpu_end - cpu_start).count();
            bench->total_cpu_time += cpu_time_delta;

            if( do_search ){
                auto gpu_start = std::chrono::high_resolution_clock::now();
                
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
                
                auto gpu_end = std::chrono::high_resolution_clock::now();
                double gpu_time_delta = std::chrono::duration<double>(gpu_end - gpu_start).count();
                bench->total_gpu_time += gpu_time_delta;
                gpu_time_this_search += gpu_time_delta;
            }
            
            // Resume CPU time tracking
            cpu_start = std::chrono::high_resolution_clock::now();

            for (int i = 0; i < THREADS; ++i) {
                for (int j = 0; j < UNROLL; j++){
                    // Nothing on queue? We rely on the producer to terminate the searching, when no more data has been added. We just skip this thread with nothing to do on it.
                    if(q_head[i] == q_tail[i]){ 
                        wasted_pmes_this_search += rows * (UNROLL - j);
                        break;  // Exit inner loop
                    }
                    current_report_seq = seq_queue[i][q_head[i]]; // No modulo needed on read
                    if(current_report_seq == settings->debug_slot) {
                        int16_t scoret1 = final_max[(i * UNROLL +j) * 2 ];
                        int16_t scoret2 = final_max[(i * UNROLL +j) * 2 + 1];
                        char aminoAcid = '@'+aa_data[i*UNROLL+j];
                        printf( "Seq:%d %c i:%d j:%d t1:%d t2:%d\n",current_report_seq, aminoAcid, seqChar, j, scoret1, scoret2);
                        seqChar++;
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
                                printf("HIT:%d,%d,%d,%d,%d\n", query, current_report_seq, score, first_hit[i],last_hit[i]-first_hit[i] );
                            }
                            else {
                                printf("Step:%7d Seq:%6d Length:%5d Score:%6d Name:%.100s\n",
                                    step, current_report_seq, data_manager->fasta_records[current_report_seq].sequence_len - 1, score, data_manager->fasta_records[current_report_seq].description);
                            }
                            if(settings->slow_output) usleep(100000);
                            finds++;
                        }
                        final_max[(i * UNROLL +j)* 2 + 1] = 0;
                        q_head[i] = (q_head[i] + 1) % (UNROLL + 1);

                        pos_reported[i] = 0;
                        first_hit[i] = -1;
                        last_hit[i] = -1;// not actually required.
                        
                        // Count completed comparison
                        comparisons_this_search++;
                    }
                }
            }
        }
    }
    
    // Final CPU time
    auto cpu_end = std::chrono::high_resolution_clock::now();
    double cpu_time_delta = std::chrono::duration<double>(cpu_end - cpu_start).count();
    bench->total_cpu_time += cpu_time_delta;
    
    auto search_end = std::chrono::high_resolution_clock::now();
    
    // Update benchmark totals
    bench->total_comparisons_computed += comparisons_this_search;
    pmes_this_search = (int64_t)step * rows * THREADS * UNROLL;
    bench->total_pmes_computed += pmes_this_search - wasted_pmes_this_search;
    bench->total_pmes_wasted += wasted_pmes_this_search;

    report_results(rows, step, finds, search_end - search_start, query, settings, data_manager, bench);
}

void report_results(int rows, int steps, int finds, std::chrono::duration<double> elapsed,
                   int query_seq, const AppSettings* settings, const DataManager* data_manager,
                   BenchmarkState* bench) {
    printf("STEP: %7d <-- Finished\n", steps);
    printf("BENCH: Searched with %4daa protein vs %8daa database; %4d finds\n", rows, steps * THREADS * UNROLL, finds);
    printf("BENCH: Execution time: %.4f seconds\n", elapsed.count());
    
    // Calculate current position in search
    int current_seq = query_seq + 1; // Next sequence to process
    
    // Calculate remaining work for current run
    int64_t pairs_yet_to_compare = bench->task_protein_comparisons - bench->total_comparisons_computed;
    int64_t pmes_yet_to_do = bench->task_pmes - bench->total_pmes_computed;

    // Calculate rates
    double total_elapsed = bench->total_cpu_time + bench->total_gpu_time;
    double proteins_per_sec = (total_elapsed > 0) ? bench->total_comparisons_computed / total_elapsed : 0;
    double pmes_per_sec = (total_elapsed > 0) ? bench->total_pmes_computed / total_elapsed : 0;
    
    double pme_waste = 100.0 * bench->total_pmes_wasted / bench->total_pmes_computed;
    // Estimate all-on-all time based on current performance
    double all_on_all_time_by_proteins = (proteins_per_sec > 0) ? 
                                         bench->total_all_on_all_comparisons / proteins_per_sec : 0;
    double all_on_all_time_by_pmes = (pmes_per_sec > 0) ? 
                                     bench->total_all_on_all_pmes / pmes_per_sec : 0;
    
    // Estimate remaining time for current run
    double remaining_time_by_proteins = (proteins_per_sec > 0) ? pairs_yet_to_compare / proteins_per_sec : 0;
    double remaining_time_by_pmes = (pmes_per_sec > 0) ? pmes_yet_to_do / pmes_per_sec : 0;
    
    // Calculate CPU percentage
    double cpu_percentage = (total_elapsed > 0) ? (bench->total_cpu_time / total_elapsed) * 100.0 : 0;
    
    printf("BENCH:\n")
    printf("BENCH:=== Benchmark Statistics ===\n");
    
    // All-on-all estimates (most important!)
    char time_buffer[128];
    format_time(all_on_all_time_by_proteins, time_buffer, sizeof(time_buffer));
    printf("BENCH: Estimated all-on-all search time: %s\n", time_buffer);
    format_time(all_on_all_time_by_pmes, time_buffer, sizeof(time_buffer));
    printf("BENCH: Estimated all-on-all search time: %s (based on PMEs)\n", time_buffer);
    
    char pps_formatted[64];
    format_number_with_commas((int64_t)proteins_per_sec, pps_formatted,sizeof(pps_formatted));
    char pmes_formatted[64];
    format_number_with_commas((int64_t)pmes_per_sec, pmes_formatted,sizeof(pmes_formatted));
    
    // Performance metrics
    printf("BENCH: Performance: %s protein-pairs/sec, %s PMEs/sec Wastage: %.1f%%\n", pps_formatted, pmes_formatted, pme_waste);
    
    // Time breakdown
    printf("BENCH: CPU time: %.1f%% (%.2fs), GPU time: %.1f%% (%.2fs)\n",
           cpu_percentage, bench->total_cpu_time,
           100.0 - cpu_percentage, bench->total_gpu_time);
    
    printf("BENCH: Pairs To Do: %lld PMEs To Do: %lld\n", pairs_yet_to_compare, pmes_yet_to_do );
    // Remaining time for current run
    if (pairs_yet_to_compare > 0) {
        format_time(remaining_time_by_proteins, time_buffer, sizeof(time_buffer));
        printf("BENCH: Time remaining (by proteins): %s\n", time_buffer);
        format_time(remaining_time_by_pmes, time_buffer, sizeof(time_buffer));
        printf("BENCH: Time remaining (by PMEs): %s\n", time_buffer);
    }
    
    printf("\n");
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