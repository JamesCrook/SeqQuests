# Build with your script first
./build.sh

# Profile with Instruments CLI (pass args after the binary)
instruments -t "Metal System Trace" ./bin/sw_search_metal --start_at 70000 --num_seqs 10

# To save the trace file
instruments -t "Metal System Trace" -D trace_output.trace ./bin/sw_search_metal --start_at 70000 --num_seqs 10