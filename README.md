# StORF-Reporter v0.4.2 - Preprint: https://www.biorxiv.org/content/10.1101/2022.03.31.486628v1

StORF-Reporter, a toolkit that takes as input an annotated genome and returns missed CDS 
genes from the Unannotated Regions (URs).
# Please use `pip3 install StORF-Reporter' to install the tool.
This will also install numpy and the 'ORForise' package from https://github.com/NickJD/ORForise to allow for additional functionality.

# StORF-Reporter (BETA) - Please raise issues at https://github.com/NickJD/StORF-Reporter/issues
This tool extracts Unnannotated Regions from PROKKA genome annotations, finds Stop - Open Reading Frames
and reports them in a new PROKKA formatted GFF file in the PROKKA output directory.

This tool is currently in BETA but can be run as: 
```console
python3 -m StORF-Reporter.StORF_Reporter -anno PROKKA -pd ../PROKKA_04062022/
```
### Menu - (python3 -m StORF-Reporter.StORF_Reporter -h):
```python
usage: StORF_Reporter.py [-h] -anno [{PROKKA,Ensembl,CDS}] [-pd PROKKA_DIR] [-min_len MINLEN]
[-max_len MAXLEN] [-ex_len EXLEN] [-olap OVERLAP_NT] [-type [{StORF,CDS,ORF}]] [-ao ALLOWED_OVERLAP] 
[-gz {True,False}] [-v {True,False}]

optional arguments:
  -h, --help            show this help message and exit
  -anno [{PROKKA,Ensembl,CDS}]
                        Default - PROKKA: Annotation type to be StORF-Reported:Options: PROKKA = 
                        "misc_RNA,gene,mRNA,CDS,tRNA,tmRNA,CRISPR";Ensembl = "ID=gene" ;CDS = "CDS"
  -pd PROKKA_DIR, --PROKKA_dir PROKKA_DIR
                        PROKKA output directory to be used if PROKKA chosen
  -min_len MINLEN       Default - 30: Minimum UR Length
  -max_len MAXLEN       Default - 100,000: Maximum UR Length
  -ex_len EXLEN         Default - 50: UR Extension Length
  -olap OVERLAP_NT      Default - 50: Maximum number of nt of a StORF which can overlap another StORF.
  -type [{StORF,CDS,ORF}]
                        Default - "StORF": Which GFF type for StORFs to be reported as in GFF (StORF,CDS,ORF)
  -ao ALLOWED_OVERLAP   Default - 50 nt: Maximum overlap between a StORF and an original gene.
  -gz {True,False}      Default - False: Output as .gz
  -v {True,False}       Default - False: Print out runtime status
```

# UR_Extractor
Python3 script to extract Unannotated Regions from DNA sequences uses FASTA and GFF files as input.

### Menu - (python3 -m StORF-Reporter.UR_Extractor -h):  
```console
python3 -m StORF-Reporter.UR_Extractor -f genomes/E-coli.fasta.gz -gff genomes/E-coli.gff -o genomes/E-coli_UR -gz True
```

```python
usage: UR_Extractor.py [-h] -f FASTA -gff GFF [-ident IDENT] [-min_len MINLEN]
                       [-max_len MAXLEN] [-ex_len EXLEN]
                       [-gene_ident GENE_IDENT] -o OUT_PREFIX
                       [-gz {True,False}]

optional arguments:
  -h, --help            show this help message and exit
  -f FASTA, --fasta_seq FASTA
                        FASTA file for Unannotated Region seq extraction
  -gff GFF              GFF annotation file for the FASTA
  -ident IDENT          Identifier given for Unannotated Region output
                        sequences: Default "Input"_UR
  -min_len MINLEN       Minimum UR Length: Default 30
  -max_len MAXLEN       Maximum UR Length: Default 100,000
  -ex_len EXLEN         UR Extension Length: Default 50
  -gene_ident GENE_IDENT
                        Identifier used for extraction of "genic" regions
                        "CDS,rRNA,tRNA": Default for Ensembl_Bacteria =
                        "ID=gene"
  -o OUT_PREFIX, --output_prefix OUT_PREFIX
                        Output file prefix - Without filetype
  -gz {True,False}      Default - False: Output as .gz
```
# StORF-Finder
Python3 script to extract Stop - Stop Codon (St)ORFs from Fasta sequences.  

### Menu - (python3 -m StORF-Reporter.StORF_Finder -h):   
```console
python3 -m StORF-Reporter.StORF_Finder -seq genomes/E-coli_UR.fasta.gz -o genomes/E-coli_UR_StORF -gz True
```

```python
usage: StORF_Finder.py [-h] -f FASTA [-ua {True,False}] [-wc {True,False}]
                       [-ps {True,False}] [-filt [{none,soft,hard}]]
                       [-aa {True,False}] [-con_storfs {True,False}]
                       [-aa_only {True,False}] [-con_only {True,False}]
                       [-stop_ident {True,False}] [-minorf MIN_ORF]
                       [-maxorf MAX_ORF] [-codons STOP_CODONS]
                       [-olap OVERLAP_NT] [-gff {True,False}] [-o OUT_PREFIX]
                       [-lw {True,False}] [-gz {True,False}] [-v {True,False}]

StORF Run Parameters.

optional arguments:
  -h, --help            show this help message and exit
  -f FASTA              Input FASTA File
  -ua {True,False}      Default - Treat input as Unannotated: Use "-ua False"
                        for standard fasta
  -wc {True,False}      Default - False: StORFs reported across entire
                        sequence
  -ps {True,False}      Default - False: Partial StORFs reported
  -filt [{none,soft,hard}]
                        Default - Hard: Filtering level none is not
                        recommended, soft for single strand filtering and hard
                        for both-strand longest-first tiling
  -aa {True,False}      Default - False: Report StORFs as amino acid sequences
  -con_storfs {True,False}
                        Default - False: Output Consecutive StORFs
  -aa_only {True,False}
                        Default - False: Only output Amino Acid Fasta
  -con_only {True,False}
                        Default - False: Only output Consecutive StORFs
  -stop_ident {True,False}
                        Default - True: Identify Stop Codon positions with '*'
  -minorf MIN_ORF       Default - 100: Minimum StORF size in nt
  -maxorf MAX_ORF       Default - 50kb: Maximum StORF size in nt
  -codons STOP_CODONS   Default - ('TAG,TGA,TAA'): List Stop Codons to use
  -olap OVERLAP_NT      Default - 50: Maximum number of nt of a StORF which
                        can overlap another StORF.
  -gff {True,False}     Default - True: StORF Output a GFF file
  -o OUT_PREFIX         Default - False/Same as input name with '_StORF-R':
                        Output filename prefix - Without filetype
  -lw {True,False}      Default - False: Line wrap FASTA sequence output at 60
                        chars
  -gz {True,False}      Default - False: Output as .gz
  -v {True,False}       Default - False: Print out runtime status
```
