#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>
#include <sys/stat.h>

#define NS_PRIVATE_IMPLEMENTATION
#define CA_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION

#include <Foundation/Foundation.hpp>
#include <Metal/Metal.hpp>
#include <QuartzCore/QuartzCore.hpp>

#define MAX_DESCRIPTION_LEN 256
#define COLS 1024

typedef struct {
    int32_t description_len;
    char* description;
    int32_t sequence_len;
    char* sequence;
} FastaRecord;

// --- Function Prototypes ---
long file_size(const char* filename);
char* read_shader_source(const char* filename);
void load_pam_data(const char* filename, int16_t* pam_data);
FastaRecord* load_fasta_data(const char* filename, int* num_records);
void release_fasta_records(FastaRecord* records, int num_records);


// --- Main ---
int main(int argc, char * argv[]) {
    @autoreleasepool {
        // --- Device Setup ---
        MTL::Device* device = MTL::CreateSystemDefaultDevice();
        if (!device) {
            fprintf(stderr, "Metal is not supported on this device.\n");
            return 1;
        }
        printf("Device: %s\n", device->name()->utf8String());

        // --- Load Data ---
        int16_t pam_data[32 * 32];
        load_pam_data("c_src/pam250.bin", pam_data);

        int num_fasta_records = 0;
        FastaRecord* fasta_records = load_fasta_data("c_src/fasta.bin", &num_fasta_records);
        if (!fasta_records) return 1;

        // Use the first FASTA record for the search
        char* search_sequence = fasta_records[0].sequence;
        int rows = fasta_records[0].sequence_len;
        printf("\nSearching with: %s\n", fasta_records[0].description);
        printf("Sequence length: %d\n", rows);

        // --- Create PAM LUT for the search sequence ---
        int16_t* pam_lut = (int16_t*)malloc(32 * rows * sizeof(int16_t));
        for (int col = 0; col < 32; ++col) {
            for (int i = 0; i < rows; ++i) {
                int aa_idx = (int)search_sequence[i] & 31;
                pam_lut[col * rows + i] = pam_data[col * 32 + aa_idx];
            }
        }

        // --- Metal Setup ---
        char* shader_source = read_shader_source("c_src/nws.metal");
        if(!shader_source) return 1;

        NS::Error* error = nullptr;
        MTL::Library* library = device->newLibrary(NS::String::string(shader_source, NS::UTF8StringEncoding), nullptr, &error);
        if (!library) {
            fprintf(stderr, "Failed to create library: %s\n", error->localizedDescription()->utf8String());
            free(shader_source);
            return 1;
        }
        free(shader_source);

        MTL::Function* kernel_function = library->newFunction(NS::String::string("nws_step", NS::UTF8StringEncoding));
        MTL::ComputePipelineState* pipeline = device->newComputePipelineState(kernel_function, &error);
        if (!pipeline) {
            fprintf(stderr, "Failed to create pipeline state: %s\n", error->localizedDescription()->utf8String());
            return 1;
        }

        MTL::CommandQueue* queue = device->newCommandQueue();

        // --- Buffer Creation ---
        printf("\n--- Initializing Metal Buffers ---\n");
        MTL::Buffer* data_buffers[2];
        data_buffers[0] = device->newBuffer(COLS * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
        data_buffers[1] = device->newBuffer(COLS * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
        memset(data_buffers[0]->contents(), 0, COLS * rows * sizeof(int16_t));
        memset(data_buffers[1]->contents(), 0, COLS * rows * sizeof(int16_t));

        MTL::Buffer* pam_buffer = device->newBuffer(pam_lut, 32 * rows * sizeof(int16_t), MTL::ResourceStorageModeShared);
        MTL::Buffer* aa_buffer = device->newBuffer(COLS * sizeof(int16_t), MTL::ResourceStorageModeShared);
        MTL::Buffer* max_buffer = device->newBuffer(COLS * 2 * sizeof(int16_t), MTL::ResourceStorageModeShared);

        uint32_t num_cols_val = COLS;
        uint32_t num_rows_val = rows;
        MTL::Buffer* cols_buffer = device->newBuffer(&num_cols_val, sizeof(uint32_t), MTL::ResourceStorageModeShared);
        MTL::Buffer* rows_buffer = device->newBuffer(&num_rows_val, sizeof(uint32_t), MTL::ResourceStorageModeShared);
        printf("Matrix: %dx%d\n", COLS, rows);
        printf("Buffers created\n");


        // --- Run Metal Steps ---
        printf("\nRunning NWS steps...\n");
        clock_t start = clock();

        int16_t* aa_data = (int16_t*)aa_buffer->contents();
        int16_t* final_max = (int16_t*)max_buffer->contents();
        memset(final_max, 0, COLS * 2 * sizeof(int16_t));

        int pos[COLS] = {0};
        int seqno[COLS];
        for(int i=0; i<COLS; ++i) seqno[i] = -1;
        int seq = -1;

        bool more_data = true;
        int step = -1;

        while(more_data) {
            step++;
            more_data = false;
            for (int i = 0; i < COLS; ++i) {
                if (seqno[i] == -1 || pos[i] >= fasta_records[seqno[i]].sequence_len) {
                    int16_t score = final_max[2 * i + 1];
                    if (score > 100) {
                        printf("Slot:%4d Seq:%6d Length:%4d Score:%5d Name:%.100s\n",
                                i, seqno[i], fasta_records[seqno[i]].sequence_len - 1, score, fasta_records[seqno[i]].description);
                    }
                    final_max[2 * i + 1] = 0;
                    seq++;
                    if (seq < num_fasta_records) {
                        pos[i] = 0;
                        seqno[i] = seq;
                    } else {
                        seqno[i] = -1;
                        continue;
                    }
                }
                aa_data[i] = fasta_records[seqno[i]].sequence[pos[i]] & 31;
                pos[i]++;
                more_data = true;
            }

            if(more_data) {
                int in_idx = step % 2;
                int out_idx = (step + 1) % 2;

                MTL::CommandBuffer* command_buffer = queue->commandBuffer();
                MTL::ComputeCommandEncoder* encoder = command_buffer->computeCommandEncoder();
                encoder->setComputePipelineState(pipeline);
                encoder->setBuffer(data_buffers[in_idx], 0, 0);
                encoder->setBuffer(data_buffers[out_idx], 0, 1);
                encoder->setBuffer(pam_buffer, 0, 2);
                encoder->setBuffer(aa_buffer, 0, 3);
                encoder->setBuffer(max_buffer, 0, 4);
                encoder->setBuffer(cols_buffer, 0, 5);
                encoder->setBuffer(rows_buffer, 0, 6);

                MTL::Size grid_size = MTL::Size(COLS, 1, 1);
                NS::UInteger threadgroup_size_val = pipeline->maxTotalThreadsPerThreadgroup();
                if (threadgroup_size_val > COLS) {
                    threadgroup_size_val = COLS;
                }
                MTL::Size threadgroup_size = MTL::Size(threadgroup_size_val, 1, 1);

                encoder->dispatchThreads(grid_size, threadgroup_size);
                encoder->endEncoding();
                command_buffer->commit();
                command_buffer->waitUntilCompleted();
            }
        }

        clock_t end = clock();
        double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
        printf("Execution time: %.4f seconds\n", elapsed);

        // --- Cleanup ---
        release_fasta_records(fasta_records, num_fasta_records);
        free(pam_lut);

        data_buffers[0]->release();
        data_buffers[1]->release();
        pam_buffer->release();
        aa_buffer->release();
        max_buffer->release();
        cols_buffer->release();
        rows_buffer->release();

        queue->release();
        pipeline->release();
        kernel_function->release();
        library->release();
        device->release();
    }
    return 0;
}

// --- Helper Functions ---

long file_size(const char* filename) {
    struct stat st;
    if (stat(filename, &st) == 0)
        return st.st_size;
    return -1;
}

char* read_shader_source(const char* filename) {
    long size = file_size(filename);
    if (size == -1) {
        fprintf(stderr, "Could not stat file %s\n", filename);
        return NULL;
    }

    FILE* file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "Could not open file %s\n", filename);
        return NULL;
    }

    char* source = (char*)malloc(size + 1);
    fread(source, 1, size, file);
    source[size] = '\0';
    fclose(file);

    return source;
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

    // Dynamically allocate records array
    int capacity = 1000;
    FastaRecord* records = (FastaRecord*)malloc(sizeof(FastaRecord) * capacity);
    int count = 0;

    while (fread(&records[count].description_len, sizeof(int32_t), 1, f) == 1) {
        if (count >= capacity) {
            capacity *= 2;
            records = (FastaRecord*)realloc(records, sizeof(FastaRecord) * capacity);
        }
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
