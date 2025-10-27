# data_munger.py should use sequences.py to read sequences and filter. 


# For example 
# Select proteins with:
# - Reviewed status (Swiss-Prot)
# - No "Uncharacterized", "Putative", "Predicted" in name
# - Have GO terms, EC numbers, or Pfam domains
# - Exclude fragments

# I would also like to be able to filter to humans, rats, e.coli, yeast, chicken
# It should be possible to run data_munger as a command line utility, or to invoke a specific job using it via job_manager