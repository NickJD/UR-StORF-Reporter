import argparse
from argparse import Namespace
import pathlib
import collections
import textwrap
import hashlib
import pyrodigal
from tempfile import NamedTemporaryFile
import os
import sys
import gzip


try:
    # Calling from ORForise via pip
    from .UR_Extractor import extractor
    from .StORF_Finder import StORF_Reported
    from .Constants import *
except (ModuleNotFoundError, ImportError, NameError, TypeError) as error:
    from UR_Extractor import extractor
    from StORF_Finder import StORF_Reported
    from Constants import *


# class StORF_obj: # TODO
#     def __init__(self, name, roll):
#         self.name = name
#         self.roll = roll

###################
gencode = {
      'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M',
      'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
      'AAC':'N', 'AAT':'N', 'AAA':'K', 'AAG':'K',
      'AGC':'S', 'AGT':'S', 'AGA':'R', 'AGG':'R',
      'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L',
      'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
      'CAC':'H', 'CAT':'H', 'CAA':'Q', 'CAG':'Q',
      'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
      'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V',
      'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
      'GAC':'D', 'GAT':'D', 'GAA':'E', 'GAG':'E',
      'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
      'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S',
      'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
      'TAC':'Y', 'TAT':'Y', 'TAA':'*', 'TAG':'*',
      'TGC':'C', 'TGT':'C', 'TGA':'*', 'TGG':'W'}

def translate_frame(sequence):
    translate = ''.join([gencode.get(sequence[3 * i:3 * i + 3], 'X') for i in range(len(sequence) // 3)])
    return translate
############################

def GFF_StoRF_write(StORF_options, Reporter_options, track_contig, gff_outfile, StORF, StORF_Num): # Consistency in outfile
    ID = track_contig + '_UR_' + StORF[0] + '_' + StORF[10] + '_'+ str(StORF[9])
    to_hash = gff_outfile.name.split('.')[0] + '_' + ID # create unique hash from outfile name and ID
    locus_tag = hashlib.shake_256(to_hash.encode()).hexdigest(8)
    if '92ce72da9665db02' in locus_tag:
        print("s")
    ### Write out new GFF entry -
    strand = StORF[7]
    start = StORF[3]
    stop = StORF[4]
    UR_Start = int(StORF[0].split('_')[0])
    start_stop = StORF[12][0:3]
    if len(StORF[11]) == 3: # fix for con-storfs
        mid = int(StORF[11]) - int(StORF[11])
        mid_stop = StORF[12][mid - 3:mid]
    else:
        mid_stop = 'N/A'
    end_stop = StORF[12][-3:]

    if strand == '+':
        gff_start = max(start + 1 + UR_Start, 1) # this may need to change to account for different exlen
        gff_stop = max(stop + UR_Start, 1)
        if UR_Start == 1:
            gff_start -= 1
            gff_stop -= 1

        if Reporter_options.stop_inclusive == False:  # To remove the start and stop codon positions.
            gff_start = gff_start + 3
        frame = (int(gff_stop) % 3) + 1
    elif strand == '-':
        gff_start = max(start - 2 + UR_Start, 1)
        gff_stop = max(stop - 3 + UR_Start, 1)
        if Reporter_options.stop_inclusive == False:  # To remove the start and stop codon positions.
            gff_stop = gff_stop - 3
        frame = (int(gff_stop) % 3) + 4

    StORF_length = int(gff_stop) + 1 - int(gff_start) # +1 to adjust for base-1

    gff_outfile.write(track_contig + '\tStORF-Reporter\t' + StORF_options.feature_type + '\t' +  str(gff_start) + '\t' + str(gff_stop) + '\t.\t' +
        StORF[7] + '\t0\tID=StORF_' + locus_tag + ';locus_tag=' + ID + ';INFO=Additional_Annotation_StORF-Reporter;UR_Stop_Locations=' + StORF[11].replace(',','-') + ';Name=' +
           StORF[10] + '_' + str(StORF_Num) + ';' + StORF[10] + '_Num_In_UR=' + str(StORF[9]) + ';' + StORF[10] + '_Length=' + str(StORF_length) + ';' + StORF[10] +
           '_Frame=' + str(frame) + ';UR_' + StORF[10] + '_Frame=' + str(StORF[6]) +  ';Start_Stop=' + start_stop + ';Mid_Stops=' + mid_stop  + ';End_Stop='
           + end_stop + ';StORF_Type=' + StORF[10] + '\n')


def FASTA_StORF_write(Reporter_options, track_contig, fasta_outfile, StORF,StORF_Num):  # Consistency in outfile
    ## This should compute the same hash as the one for GFF_Write - Should not be computed twice though
    ID = track_contig + '_UR_' + StORF[0] + '_' + StORF[10] + '_'+ str(StORF[9])
    to_hash = fasta_outfile.name.split('.')[0] + '_' + ID # create unique hash from outfile name and ID
    locus_tag = 'StORF_' + hashlib.shake_256(to_hash.encode()).hexdigest(8)
    ### Wrtie out new FASTA entry - Currently only write out as nt
    fasta_outfile.write('>'+locus_tag+'\n')
    #amino = translate_frame(StORF[-1][0:])
    #if Reporter_options.remove_stop == True:
    #    amino = amino.strip('*')
    #wrapped = textwrap.wrap(amino, width=60)
    wrapped = textwrap.wrap(StORF[-1], width=60)
    for wrap in wrapped:
        fasta_outfile.write(wrap + '\n')
    if Reporter_options.storfs_out == True: # clean this
        amino = translate_frame(StORF[-1][0:])
        if Reporter_options.remove_stop == True:
            amino = amino.strip('*')
        storf_fasta_outfile = open(str(fasta_outfile.name).replace('.fasta','_StORFs_Only.fasta'),'a') #wa not good
        storf_fasta_outfile.write('>' + locus_tag + '\n')
        storf_fasta_outfile.write(amino+'\n')
        # for wrap in wrapped:
        #     storf_fasta_outfile.write(wrap + '\n')

def FASTA_Load(faa_infile,ffn_infile):
    ### Coding sequences first
    PROKKA_AA = collections.defaultdict()
    first = True
    infile = open(faa_infile)
    seq = ''
    ##load in fasta file and make dict of seqs and ids
    for line in infile:
        line = line.strip()
        if line.startswith('>') and first == False:
            PROKKA_AA.update({id:seq})
            id = line.replace('>','')
            id = id.split(' ')[0]
            seq = ''
        elif line.startswith('>'):
            id = line.replace('>','')
            id = id.split(' ')[0]
            first = False
        else:
            seq += line
    PROKKA_AA.update({id:seq})
    ### Coding and Non-Coding sequences in NT form next
    PROKKA_NT = collections.defaultdict()
    first = True
    infile = open(ffn_infile)
    seq = ''
    ##load in fasta file and make dict of seqs and ids
    for line in infile:
        line = line.strip()
        if line.startswith('>') and first == False:
            PROKKA_NT.update({id:seq})
            id = line.replace('>','')
            id = id.split(' ')[0]
            seq = ''
        elif line.startswith('>'):
            id = line.replace('>','')
            id = id.split(' ')[0]
            first = False
        else:
            seq += line
    PROKKA_NT.update({id:seq})

    return PROKKA_AA,PROKKA_NT

def read_pyrodigal_fasta(fasta_in,sequences):
    first = True
    for line in fasta_in:
        line = line.strip()
        if line.startswith(';'):
            continue
        elif line.startswith('>') and not first:
            sequences.update({sequence_name: seq})
            seq = ''
            sequence_name = line.split(' ')[0].replace('>', '')
        elif line.startswith('>'):
            seq = ''
            sequence_name = line.split(' ')[0].replace('>', '')
        else:
            seq += str(line)
            first = False
        sequences.update({sequence_name: seq})
    return sequences

def pyrodigal_predict(fasta,Reporter_options):
    sequences = collections.OrderedDict()
    try:  # Detect whether fasta/gff files are .gz or text and read accordingly
        fasta_in = gzip.open(fasta, 'rt')
        sequences = read_pyrodigal_fasta(fasta_in, sequences)
    except:
        fasta_in = open(fasta, 'r', encoding='unicode_escape')  # Not sure if needed in long term
        sequences = read_pyrodigal_fasta(fasta_in, sequences)
    pyrodigal_hold = NamedTemporaryFile(mode='w+', delete=False)

    if Reporter_options.py_out == True:
        pyrodigal_out = fasta.split('.')[0]
        pyrodigal_out_file = open(pyrodigal_out+'_Pyrodigal.gff','w')

    orf_finder = pyrodigal.OrfFinder()
    longest = (max(sequences.values(), key=len)) # Get longest contig for training
    if Reporter_options.py_train == 'longest':
        orf_finder.train(longest)
    for sequence_name, seq in sequences.items():
        if Reporter_options.py_train == 'indvidual':
            try:  # Catch if sequence is less than 20kb - will run in meta mode
                orf_finder.train(seq)
                break
            except ValueError:
                orf_finder = pyrodigal.OrfFinder(meta=True)  # If NO contig is >= 20kb#
        else:
            genes = orf_finder.find_genes(seq)
        if Reporter_options.py_out == True:
            genes.write_gff(pyrodigal_out_file, sequence_id=sequence_name)
        genes.write_gff(pyrodigal_hold, sequence_id=sequence_name)

    pyrodigal_out_file.close()
    pyrodigal_hold.close()
    Reporter_options.gff = pyrodigal_hold
    Reporter_options.fasta = fasta
    URs = extractor(Reporter_options)
    return URs, Reporter_options




def run_UR_Extractor_path(Reporter_options): # When given a single PROKKA/Bakta Directory
    fasta = list(pathlib.Path(Reporter_options.path).glob('*.fna'))
    fasta = str(fasta[0])
    Reporter_options.fasta = fasta
    gff_list = list(pathlib.Path(Reporter_options.path).glob('*.gff'))
    gff_list.extend(pathlib.Path(Reporter_options.path).glob('*.gff3'))
    for gff in gff_list: # Poor checking method - must change
        if '_StORF-Reporter' not in str(gff): # Might fall over
            gff = str(gff)
            Reporter_options.gff = gff
    URs = extractor(Reporter_options)
    return URs,Reporter_options


def run_UR_Extractor_Combined_GFFs(Reporter_options,gff): # When given a directory with multiple GFFs but without accompianing .fna
    if '_StORF-Reporter' not in str(gff): #Might fall over - put a break
        gff = str(gff)
        Reporter_options.gff = gff
    Reporter_options.fasta = gff
    URs = extractor(Reporter_options)
    return URs,Reporter_options

def run_UR_Extractor_Matched(Reporter_options,gff): # When given a directory with multiple GFFs but with accompianing .fna
    if '_StORF-Reporter' not in str(gff): #Might fall over - put a break
        gff = str(gff)
        Reporter_options.gff = gff
        fasta = gff.replace('.gff','.fasta')
        fna = gff.replace('.gff', '.fna')
        fa = gff.replace('.gff', '.fa')
        if os.path.isfile(fasta):
            Reporter_options.fasta = fasta
        elif os.path.isfile(fna):
            Reporter_options.fasta = fna
        elif os.path.isfile(fa):
            Reporter_options.fasta = fa
        else:
            sys.exit('No matching FASTA file found for ' + gff)
    URs = extractor(Reporter_options)
    return URs,Reporter_options

def run_UR_Extractor_GFF(Reporter_options, fasta, gff): # When given a directory with multiple GFFs but without accompianing .fna
    if '_StORF-Reporter' not in str(gff): #Might fall over - put a break
        gff = str(gff)
        Reporter_options.gff = gff
    fasta = str(fasta)
    Reporter_options.fasta = fasta
    URs = extractor(Reporter_options)
    return URs,Reporter_options

def find_prev_StORFs(StORF_options, Reporter_options, Contig_URs, track_current_start, track_prev_stop, track_contig):
    StORFs_to_del = []
    StORFs = []
    is_break = False
    try:
        current_Contig_URs = Contig_URs[track_contig]
        for StORF_Num, data in current_Contig_URs.items():
            if is_break == True:
                break
            if data != None:
                ur_pos = data[8] # extended UR
                ur_start = int(ur_pos.split('_')[0])
                StORF_Stop_Pos = data[0]
                StORF_Start_In_UR = int(StORF_Stop_Pos.split(',')[0])
                StORF_Stop_In_UR = int(StORF_Stop_Pos.split(',')[-1])
                ur_frame = data[2]
                strand = data[3]
                gff_start = str(StORF_Start_In_UR + 1 + max(ur_start - Reporter_options.exlen, 0))
                gff_stop = str(StORF_Stop_In_UR + max(ur_start - Reporter_options.exlen, 0))
                allow_start = int(gff_start) + StORF_options.allowed_overlap
                allow_stop = int(gff_stop) - StORF_options.allowed_overlap
                StORF_Seq = data[1]
                StORF_Length = data[4]
                StORF_UR_Num = data[6]
                if allow_stop <= track_current_start:# and allow_start >= track_prev_stop:
                    if strand == '+': # Get original genome frame
                        frame = (int(gff_start) % 3) + 1
                    elif strand == '-':
                        frame = (int(gff_stop) % 3) + 4
                    StORFs.append([ur_pos,gff_start,gff_stop,StORF_Start_In_UR,StORF_Stop_In_UR,frame,ur_frame,strand,
                                   StORF_Length,StORF_UR_Num,data[5],StORF_Stop_Pos,StORF_Seq])
                    if StORF_Num not in StORFs_to_del:
                        StORFs_to_del.append(StORF_Num)
                elif allow_start > track_current_start: # Check
                    is_break = True
                    break

        for StORF in StORFs_to_del:
            del current_Contig_URs[StORF]
        Contig_URs[track_contig] = current_Contig_URs # Just incase shallow copy does not remove StORF for us
    ### Might need to force remove more ur storfs regions

        return StORFs, Contig_URs

    except KeyError:
        if StORF_options.verbose == True:
            print("GFF formatting error - Something wrong with seqeunce region " + track_contig)
        return StORFs, Contig_URs


def find_after_StORFs(StORF_options,Contig_URs,track_current_start,track_current_stop, track_contig):
    StORFs = []
    is_break = False
    try:
        current_Contig_URs = Contig_URs[track_contig]
        for StORF_Num, data in current_Contig_URs.items():
            if is_break == True:
                break
            if data != None:
                # for UR_StORF, UR_StORF_data in UR_StORFs.items():
                ur_pos = data[8] # extended UR
                StORF_Stop_Pos = data[0]
                StORF_Start_In_UR = int(StORF_Stop_Pos.split(',')[0])
                StORF_Stop_In_UR = int(StORF_Stop_Pos.split(',')[-1])
                ur_frame = data[2]
                strand = data[3]
                key_start = int(ur_pos.split('_')[0])
                StORF_start = key_start + StORF_Start_In_UR
                StORF_stop = key_start + StORF_Stop_In_UR
                allow_start = StORF_start + StORF_options.allowed_overlap
                StORF_Seq = data[1]
                StORF_Length = data[4]
                StORF_UR_Num = data[6]
            if allow_start >= track_current_stop:
                gff_start = str(StORF_Start_In_UR + int(ur_pos.split('_')[-1].split('_')[0]))
                gff_stop = str(StORF_Stop_In_UR + int(ur_pos.split('_')[-1].split('_')[0]))
                if strand == '+':  # Get original genome frame
                    frame = (int(gff_start) % 3) + 1
                elif strand == '-':
                    frame = (int(gff_stop) % 3) + 4
                StORFs.append(
                    [ur_pos, StORF_start, StORF_stop, StORF_Start_In_UR, StORF_Stop_In_UR, frame, ur_frame, strand,
                     StORF_Length, StORF_UR_Num, data[5], StORF_Stop_Pos, StORF_Seq])

        return StORFs
    except KeyError:
        if StORF_options.verbose == True:
            print("GFF formatting error - Something wrong with sequence region " + track_contig)
        return StORFs

def StORF_Filler(StORF_options, Reporter_options, Reported_StORFs):
    if Reporter_options.pyrodigal == True:
        with open(StORF_options.gff.name, "r") as gff:
            gff_in = gff.read()
            gff_name = Reporter_options.path.split('.')[0]
    else:
        with open(StORF_options.gff, 'r') as tmp_in:
            gff_in = tmp_in.read()
        gff_name = StORF_options.gff
    outfile = open(gff_name.replace('.gff','') + '_StORF-Reporter_Combined.gff', 'w')
    track_prev_contig, track_contig = '',''
    StORF_Num = 0
    end = False
    written_line = None
    Contig_URS = collections.defaultdict()
    for Contig, URs in Reported_StORFs.items():
        UR_StORF_Num = 0
        Contig_StORFs = collections.OrderedDict()
        for UR in URs:
            for StORF, data in UR.items():
                data.insert(0, StORF)
                Contig_StORFs.update({UR_StORF_Num: data})
                UR_StORF_Num += 1

        Contig_URS[Contig] = Contig_StORFs
    ### Rename .gff to .fasta / faa and load in fasta file
    if StORF_options.path == True: # If normal PROKKA Dir run
        fasta_outfile = gff_name.replace('.gff3','').replace('.gff','')
        fasta_outfile = open(fasta_outfile + '_StORF-Reporter_Combined.fasta','w')
        faa_infile = StORF_options.gff.replace('.gff3', '.faa').replace('.gff','.faa')
        ffn_infile = StORF_options.gff.replace('.gff3', '.ffn').replace('.gff','.ffn')
        Original_AA,Original_NT = FASTA_Load(faa_infile,ffn_infile)
    if Reporter_options.pyrodigal == True:
        outfile.write('##Pyrodigal annotation and StORF-Reporter extended GFF annotation of ' + gff_name.split('/')[-1] + '\n')
    else:
        outfile.write('##StORF-Reporter extended GFF annotation of ' + gff_name.split('/')[-1] + '\n')
    outfile.write('##StORF-Reporter ' + StORF_Reporter_Version + '\n')

    first_region = True
    for line in gff_in.splitlines( ):
        if not line.startswith('#') and end == False:
            data = line.split('\t')
            track_current_start = int(data[3])
            track_current_stop = int(data[4])
            track_contig = data[0]
            if data[2] == 'region':
                outfile.write(line.strip() + '\n')
                first_region = False
                continue
            if track_contig != track_prev_contig:  # End of current contig
                # if track_prev_contig != '': # Get last StORF on Contig - If Present
                #     StORFs = find_after_StORFs(StORF_options, Contig_URS, track_prev_start, track_prev_stop,track_prev_contig) # Changed to prev stop because we are switching from previous contig
                #     if StORFs:
                #         for StORF in StORFs:
                #             GFF_StoRF_write(StORF_options, Reporter_options, track_prev_contig, outfile, StORF,
                #                             StORF_Num)  # To keep consistency
                #             if StORF_options.path == True:
                #                 FASTA_StORF_write(Reporter_options, track_contig, fasta_outfile, StORF,StORF_Num)
                #             StORF_Num += 1
                track_prev_start, track_prev_stop = 0, 0
            track_prev_contig = track_contig
            if track_current_start == track_prev_start and track_current_stop == track_prev_stop:  # `duplicate' entry in GFF
                if StORF_options.verbose == True:
                    print("skip")
            else:
                StORFs, Contig_URS = find_prev_StORFs(StORF_options, Reporter_options, Contig_URS, track_current_start, track_prev_stop, track_contig)
            track_prev_start = track_current_start
            track_prev_stop = track_current_stop
            ##### Print out PROKKA/Bakta Gene
            if ('gene' in data[2] or 'ID=' in data[8]) and StORF_options.path == True:
                Original_ID = data[8].split(';')[0].replace('ID=','').replace('_gene','')
                try:
                    Original_Seq = Original_NT[Original_ID] # used to be AA but changed for to NT. CHECK
                except KeyError:
                    try:
                        Original_Seq = Original_NT[Original_ID]
                    except KeyError:
                        if StORF_options.verbose == True:
                            print("Original seq " + Original_ID + " not found")
                fasta_outfile.write('>'+Original_ID+'\n')
                wrapped = textwrap.wrap(Original_Seq, width=60)
                for wrap in wrapped:
                    fasta_outfile.write(wrap + '\n')
            if StORFs:
                for StORF in StORFs:  # ([ur_pos,StORF_start, StORF_stop, StORF_Start_In_UR, StORF_Stop_In_UR, frame, ur_frame, strand, StORF_Length, StORF_UR_Num, StORF_Seq)]
                    GFF_StoRF_write(StORF_options, Reporter_options, track_contig, outfile, StORF, StORF_Num)  # To keep consistency
                    if StORF_options.path == True:
                        FASTA_StORF_write(Reporter_options, track_contig, fasta_outfile, StORF,StORF_Num)
                    StORF_Num += 1
            if line != written_line:
                outfile.write(line.strip()+'\n')
                written_line = line
            StORFs = None
        elif line.startswith('##sequence-region') and first_region != True:
            StORFs = find_after_StORFs(StORF_options, Contig_URS, track_prev_start, track_prev_stop,
                                       track_prev_contig)  # Changed to prev stop because we are switching from previous contig
            if StORFs:
                for StORF in StORFs:
                    GFF_StoRF_write(StORF_options, Reporter_options, track_prev_contig, outfile, StORF,
                                    StORF_Num)  # To keep consistency
                    if StORF_options.path == True:
                        FASTA_StORF_write(Reporter_options, track_contig, fasta_outfile, StORF, StORF_Num)
                    StORF_Num += 1
            outfile.write(line.strip() + '\n')

        elif line.startswith('##FASTA'):
            end = True
            # StORFs = find_after_StORFs(StORF_options, Contig_URS, track_prev_start, track_prev_stop, track_prev_contig)  # Changed to prev stop because we are switching from previous contig
            # if StORFs:
            #     for StORF in StORFs:
            #         GFF_StoRF_write(StORF_options, Reporter_options, track_prev_contig, outfile, StORF, StORF_Num)  # To keep consistency
            #         if StORF_options.path == True:
            #             FASTA_StORF_write(Reporter_options, track_contig, fasta_outfile, StORF,StORF_Num)
            #         StORF_Num += 1
            # if line != written_line:
            #     outfile.write(line.strip()+'\n')
            #     written_line = line

        else: # Now we just print out the remaining lines in the GFF
            outfile.write(line.strip()+'\n')
            written_line = line
##############################################################



def main():
    print("Thank you for using StORF-Reporter\nPlease report any issues to: https://github.com/NickJD/StORF-Reporter/issues\n#####")

    parser = argparse.ArgumentParser(description='StORF-Reporter ' + StORF_Reporter_Version + ': StORF-Reporter Run Parameters.')
    parser._action_groups.pop()

    required = parser.add_argument_group('Required Arguments')
    required.add_argument('-anno', action='store', dest='annotation_type', required=True,
                        choices=['PROKKA', 'Bakta', 'Ensembl', 'CDS', 'Pyrodigal'], nargs='?',
                        help='Annotation Type - '
                             'Options: PROKKA = Default PROKKA GFF format; '
                             ' Bakta = Default Bakta GFF format;'
                             ' Ensembl = 9th Column "ID=gene";'
                             ' CDS = 3rd Column Feature Type "CDS";'
                             ' Pyrodigal = Run Pyrodigal then StORF-Reporter')

    required.add_argument('-it', action='store', dest='input_type', required=True,
                        choices=['Out_Dir', 'Comb_GFFs', 'Matched', 'Single_Genome', 'FASTA'], nargs='?',
                        help='Type of input to be loaded by StORF-Reporter: '
                             'Options: Out_Dir = Single PROKKA or Bakta output directory;'
                             ' Comb_GFFs = Directory containing multiple GFF-FASTA combined files;'
                             ' Matched = Directory containing multiple GFF and FASTA files to be matched on filename;'
                             ' Single_Genome = Comma separated FASTA and GFF file paths for a single genome;'
                             ' FASTA = Genomic FASTA file(s) to undergo Pyrodigal and StORF-Reporter annotation - '
                             'Provide either a single filepath or a directory with multiple ".fasta/.fna/.fa" files;')

    required.add_argument('-p', action='store', dest='path', default='', required=True,
                        help='Provide one of the following; a PROKKA/Bakta output directory, a directory with multiple GFFs to be '
                             'processed, the full paths to a matching genomic FASTA and GFF separated with a comma, or a single genomic FASTA file.')

    optional = parser.add_argument_group('Optional Arguments')
    # optional.add_argument('-col', action='store', dest='genome_collection', default='', required=False,
    #                     help='Provide directories containing a collection of matching FASTA and GFF files'
    #                          '(list .fa then .gff containing directories separated by commas - ./FA,./GFF)')
    #optional.add_argument('-comb', action='store', dest='combined_gffs', default='', required=False,
    #                    help='Provide directory containing GFFs with sequences combined into single file to be StORFed - Only produces modified GFFs')
    optional.add_argument('-spos', action="store", dest='stop_inclusive', default=False, type=eval, choices=[True, False],
                        help='Default - False: Print out StORF positions inclusive of first stop codon')
    optional.add_argument('-rs', action="store", dest='remove_stop', default=True, type=eval, choices=[True, False],
                        help='Default - True: Remove stop "*" from StORF amino acid sequences')

    optional.add_argument('-sout', action="store", dest='storfs_out', default=False, type=eval, choices=[True, False],
                        help='Default - False: Print out StORF sequences separately?')

    optional.add_argument('-con_storfs', action="store", dest='con_storfs', default=False, type=eval, choices=[True, False],
                        help='Default - False: Output Consecutive StORFs')
    optional.add_argument('-con_only', action="store", dest='con_only', default=False, type=eval, choices=[True, False],
                        help='Default - False: Only output Consecutive StORFs')

    optional.add_argument('-short_storfs', action="store", dest='short_storfs', default=False, type=str, choices=['False', 'Nolap', 'Olap'],
                        help='Default - False: Run StORF-Finder in "Short-StORF" mode. Will only return StORFs between 30 and 120 nt '
                             'that do not overlap longer StORFs - Only works with StORFs for now. "Nolap" will filter Short-StORFs which are'
                             'overlapped by StORFs and Olap will report Short-StORFs which do overlap StORFs. Overlap is defined by "-olap".')
    optional.add_argument('-short_storfs_only', action="store", dest='short_storfs_only', default=False, type=eval, choices=[True, False],
                        help='Default - True. Only report Short-StORFs?')
    optional.add_argument('-min_len', action='store', dest='minlen', default='30', type=int,
                        help='Default - 30: Minimum UR Length')
    optional.add_argument('-max_len', action='store', dest='maxlen', default='100000', type=int,
                        help='Default - 100,000: Maximum UR Length')
    optional.add_argument('-ex_len', action='store', dest='exlen', default='50', type=int,
                        help='Default - 50: UR Extension Length')
    optional.add_argument('-minorf', action="store", dest='min_orf', default=100, type=int,
                        help='Default - 100: Minimum StORF size in nt')
    optional.add_argument('-olap_filt', action='store', dest='olap_filtering', default='both-strand', const='both-strand', nargs='?',
                        choices=['none', 'single-strand', 'both-strand'],
                        help='Default - "both-strand": Filtering level "none" is not recommended, "single-strand" for single strand filtering '
                             'and both-strand for both-strand longest-first tiling')
    optional.add_argument('-start_filt', action="store", dest='start_filtering', default=False, type=eval, choices=[True, False],
                        help='Default - False: Filter out StORFs without at least one of the 3 common start codons (best used for short-storfs).')
    optional.add_argument('-type', action='store', dest='feature_type', default='CDS', const='CDS', nargs='?',
                        choices=['StORF', 'CDS', 'ORF'],
                        help='Default - "CDS": Which GFF feature type for StORFs to be reported as in GFF - '
                             '"CDS" is probably needed for use in tools such as Roary')
    optional.add_argument('-olap', action="store", dest='overlap_nt', default=50, type=int,
                        help='Default - 50: Maximum number of nt of a StORF which can overlap another StORF.')
    optional.add_argument('-ao', action="store", dest='allowed_overlap', default=50, type=int,
                        help='Default - 50 nt: Maximum overlap between a StORF and an original gene.')

    prodigal_options = parser.add_argument_group('Pyrodigal Arguments:')
    prodigal_options.add_argument('-py_train', action='store', dest='py_train', required=False,
                        choices=['longest', 'individual'], nargs='?', default='longest',
                        help='Default - longest: Type of model training to be done for Pyrodigal CDS prediction: '
                             'Options: longest = Trains on longest contig;'
                             ' individual = Trains on each contig separately - runs in meta mode if contig is < 20KB')
    prodigal_options.add_argument('-po', action="store", dest='py_out', default=False, type=eval, choices=[True, False],
                        help='Default - False: Output initial Pyrodigal CDS predictions in GFF format')

    output = parser.add_argument_group('StORF-Reporter Output:')

    output.add_argument('-lw', action="store", dest='line_wrap', default=True, type=eval, choices=[True, False],
                        help='Default - True: Line wrap FASTA sequence output at 60 chars')
    output.add_argument('-aa', action="store", dest='translate', default=False, type=eval, choices=[True, False],
                        help='Default - False: Report StORFs as amino acid sequences')
    output.add_argument('-gff_fasta', action="store", dest='gff_fasta', default=False, type=eval, choices=[True, False],
                        help='Default - False: Report all gene sequences (nt) at the bottom of GFF files in PROKKA output mode')
    output.add_argument('-gz', action='store', dest='gz', default='False', type=eval, choices=[True, False],
                        help='Default - False: Output as .gz')

    misc = parser.add_argument_group('Misc:')

    misc.add_argument('-v', action='store', dest='verbose', default='False', type=eval, choices=[True, False],
                        help='Default - False: Print out runtime status')
    parser.add_argument('-nout', action='store', dest='nout', default='True', type=eval, choices=[True, False],
                        help=argparse.SUPPRESS)
    parser.add_argument('-pyrodigal', action='store', dest='pyrodigal', default='False', type=eval, choices=[True, False],
                        help=argparse.SUPPRESS)
    parser.add_argument('-nout_pyrodigal', action='store', dest='nout_pyrodigal', default='True', type=eval, choices=[True, False],
                        help=argparse.SUPPRESS)

    Reporter_options = parser.parse_args()

    #parser.error('')

    ######### Setup for PROKKA/Bakta output directory
    if (Reporter_options.annotation_type == 'PROKKA' or Reporter_options.annotation_type == 'Bakta') and Reporter_options.input_type == "Out_Dir":
        Reporter_options.gene_ident = "misc_RNA,gene,mRNA,CDS,rRNA,tRNA,tmRNA,CRISPR,ncRNA,regulatory_region,oriC"
        Contigs, Reporter_options = run_UR_Extractor_path(Reporter_options)
        ################## Find StORFs in URs - Setup StORF_Reporter-Finder Run
        StORF_options = Namespace(reporter=True, gff=Reporter_options.gff, stop_codons="TGA,TAA,TAG",
                                  partial_storf=False, whole_contig=False, storf_order='start_pos',
                                  short_storfs=Reporter_options.short_storfs, short_storfs_only=Reporter_options.short_storfs_only,
                                  con_storfs=Reporter_options.con_storfs, con_only=Reporter_options.con_only,
                                  max_orf=50000, olap_filtering='both-strand', start_filtering=False, stop_inclusive=False,
                                  feature_type=Reporter_options.feature_type, overlap_nt=Reporter_options.overlap_nt,
                                  allowed_overlap=Reporter_options.allowed_overlap, path=True,
                                  gff_fasta=Reporter_options.gff_fasta,
                                  minlen=30, maxlen=100000, min_orf=Reporter_options.min_orf, verbose=False, nout=True,
                                  pyrodigal=False,nout_pyrodigal=Reporter_options.py_out)

        Reporter_StORFs = StORF_Reported(StORF_options, Contigs)
        StORF_Filler(StORF_options, Reporter_options, Reporter_StORFs)
        print("Finished: " + Reporter_options.gff.split('.')[0])

    ######### Setup for directory of multiple PROKKA/Bakta GFFs
    elif (Reporter_options.annotation_type== 'PROKKA' or Reporter_options.annotation_type == 'Bakta') and Reporter_options.input_type  == "Comb_GFFs":
        Reporter_options.gene_ident = "misc_RNA,gene,mRNA,CDS,rRNA,tRNA,tmRNA,CRISPR,ncRNA,regulatory_region,oriC"
        Reporter_options.nout = True
        gff_list = list(pathlib.Path(Reporter_options.path).glob('*.gff'))
        gff_list.extend(pathlib.Path(Reporter_options.path).glob('*.gff3'))
        for gff in gff_list:
            Contigs, Reporter_options = run_UR_Extractor_Combined_GFFs(Reporter_options,gff)
            ################## Find StORFs in URs - Setup StORF_Reporter-Finder Run
            StORF_options = Namespace(reporter=True, gff=Reporter_options.gff, stop_codons="TGA,TAA,TAG",
                                      partial_storf=False, whole_contig=False,
                                      short_storfs=Reporter_options.short_storfs,short_storfs_only=Reporter_options.short_storfs_only,
                                      con_storfs=Reporter_options.con_storfs, con_only=Reporter_options.con_only,
                                      max_orf=50000, olap_filtering='both-strand', start_filtering=False,
                                      feature_type=Reporter_options.feature_type, storf_order='start_pos',
                                      overlap_nt=Reporter_options.overlap_nt, path='',
                                      allowed_overlap=Reporter_options.allowed_overlap,
                                      gff_fasta=Reporter_options.gff_fasta,
                                      minlen=30, maxlen=100000, min_orf=Reporter_options.min_orf, verbose=False, nout=True,
                                      pyrodigal=False,nout_pyrodigal=Reporter_options.py_out)
            Reporter_StORFs = StORF_Reported(StORF_options, Contigs)
            #sequence_id, all_StORFs = StORF_Reported(URs, StORF_options)
            StORF_Filler(StORF_options, Reporter_options, Reporter_StORFs)
            print("Finished: " + gff.name) # Will add number of additional StORFs here

    ###### Run StORF-Reporter on a single Genome with a separate FASTA and GFF file
    elif Reporter_options.input_type  == "Single_Genome":
        if Reporter_options.annotation_type == 'Ensembl':
            Reporter_options.gene_ident = "ID=gene"
        elif Reporter_options.annotation_type == 'CDS':
            Reporter_options.gene_ident = "CDS"
        else:
            Reporter_options.gene_ident = "misc_RNA,gene,mRNA,CDS,rRNA,tRNA,tmRNA,CRISPR,ncRNA,regulatory_region,oriC"  #PROKKA/Bakta
        Reporter_options.nout = True
        fasta = Reporter_options.path.split(',')[0]
        gff = Reporter_options.path.split(',')[1]
        if gff and fasta:
            if Reporter_options.verbose == True:
                print("Starting: " + str(gff))
        else:
            parser.error('"-it Single_Genome" requires comma separated FASTA and GFF filepaths')
        if gff and fasta:
            Contigs, Reporter_options = run_UR_Extractor_GFF(Reporter_options, fasta, gff)
            ################## Find StORFs in URs - Setup StORF_Reporter-Finder Run
            StORF_options = Namespace(reporter=True, gff=Reporter_options.gff, stop_codons="TGA,TAA,TAG",
                                      partial_storf=False, whole_contig=False,
                                      short_storfs=Reporter_options.short_storfs,short_storfs_only=Reporter_options.short_storfs_only,
                                      con_storfs=Reporter_options.con_storfs, con_only=Reporter_options.con_only,
                                      max_orf=50000, olap_filtering='both-strand', start_filtering=False, stop_inclusive=False,
                                      feature_type=Reporter_options.feature_type, storf_order='start_pos',
                                      overlap_nt=Reporter_options.overlap_nt, path='',
                                      allowed_overlap=Reporter_options.allowed_overlap,
                                      gff_fasta=Reporter_options.gff_fasta,
                                      minlen=30, maxlen=100000, min_orf=Reporter_options.min_orf, verbose=False, nout=True,
                                      pyrodigal=False,nout_pyrodigal=Reporter_options.py_out)
            Reporter_StORFs = StORF_Reported(StORF_options, Contigs)
            #sequence_id, all_StORFs = StORF_Reported(URs, StORF_options)
            StORF_Filler(StORF_options, Reporter_options, Reporter_StORFs)  # Append StORFs to current GFF file from provided genome annotation
            if Reporter_options.verbose == True:
                print("Finished: " + gff) # Will add number of additional StORFs here

    ############ Run StORF-Reporter on multiple non PROKKA/Bakta GFFs
    elif (Reporter_options.annotation_type == 'Ensembl' or Reporter_options.annotation_type == 'CDS') and (Reporter_options.input_type  == "Comb_GFFs"\
            or Reporter_options.input_type  == "Matched"):
        if Reporter_options.annotation_type == 'Ensembl':
            Reporter_options.gene_ident = "ID=gene"
        elif Reporter_options.annotation_type == 'CDS':
            Reporter_options.gene_ident = "CDs"
        gff_list = list(pathlib.Path(Reporter_options.path).glob('*.gff'))
        gff_list.extend(pathlib.Path(Reporter_options.path).glob('*.gff3'))
        for gff in gff_list:
            if Reporter_options.verbose == True:
                print("Starting: " + str(gff))
            if Reporter_options.input_type == "Comb_GFFs":
                Contigs, Reporter_options = run_UR_Extractor_Combined_GFFs(Reporter_options,gff)
            elif Reporter_options.input_type  == "Matched":
                Contigs, Reporter_options = run_UR_Extractor_Matched(Reporter_options, gff)
            ################## Find StORFs in URs - Setup StORF_Reporter-Finder Run
            StORF_options = Namespace(reporter=True, gff=Reporter_options.gff, stop_codons="TGA,TAA,TAG",
                                      partial_storf=False, whole_contig=False,
                                      short_storfs=Reporter_options.short_storfs,short_storfs_only=Reporter_options.short_storfs_only,
                                      con_storfs=Reporter_options.con_storfs, con_only=Reporter_options.con_only,
                                      max_orf=50000, olap_filtering='both-strand', start_filtering=False, stop_inclusive=False,
                                      feature_type=Reporter_options.feature_type, storf_order='start_pos',
                                      overlap_nt=Reporter_options.overlap_nt, path='',
                                      allowed_overlap=Reporter_options.allowed_overlap,
                                      gff_fasta=Reporter_options.gff_fasta,
                                      minlen=30, maxlen=100000, min_orf=Reporter_options.min_orf, verbose=False, nout=True,
                                      pyrodigal=False,nout_pyrodigal=Reporter_options.py_out)
            Reporter_StORFs = StORF_Reported(StORF_options, Contigs)
            #sequence_id, all_StORFs = StORF_Reported(URs, StORF_options)
            StORF_Filler(StORF_options, Reporter_options, Reporter_StORFs)  # Append StORFs to current GFF file from provided genome annotation
            if Reporter_options.verbose == True:
                print("Finished: " + gff) # Will add number of additional StORFs here

    ####### Run Pyrodigal and then StORF-Reporter on either a single or directory of FASTA files
    elif Reporter_options.annotation_type == 'Pyrodigal' and Reporter_options.input_type  == "FASTA":  # needs cleaning
        Reporter_options.gene_ident = "gene"
        if os.path.isdir(Reporter_options.path):
            fasta_list = list(pathlib.Path(Reporter_options.path).glob('*.fasta'))
            fasta_list.append(list(pathlib.Path(Reporter_options.path).glob('*.fna')))
            fasta_list.append(list(pathlib.Path(Reporter_options.path).glob('*.fa')))
        elif os.path.isfile(Reporter_options.path):
            fasta_list = [Reporter_options.path]
        else:
            parser.error('Please provide a directory or file path.')
        for fasta in fasta_list:
            if Reporter_options.verbose == True:
                print("Starting: " + str(fasta))
            ###### Run Pyrodigal
            Contigs, Reporter_options = pyrodigal_predict(fasta,Reporter_options) # run_UR_Extractor_Combined_GFFs(Reporter_options,gff)
            ################## Find StORFs in URs - Setup StORF_Reporter-Finder Run
            StORF_options = Namespace(reporter=True, gff=Reporter_options.gff, stop_codons="TGA,TAA,TAG",
                                      partial_storf=False, whole_contig=False,
                                      short_storfs=Reporter_options.short_storfs,short_storfs_only=Reporter_options.short_storfs_only,
                                      con_storfs=Reporter_options.con_storfs, con_only=Reporter_options.con_only,
                                      max_orf=50000, olap_filtering='both-strand', start_filtering=False, stop_inclusive=False,
                                      feature_type=Reporter_options.feature_type, storf_order='start_pos',
                                      overlap_nt=Reporter_options.overlap_nt, path='',
                                      allowed_overlap=Reporter_options.allowed_overlap,
                                      gff_fasta=Reporter_options.gff_fasta,
                                      minlen=30, maxlen=100000, min_orf=Reporter_options.min_orf, verbose=False, nout=True,
                                      pyrodigal=True,nout_pyrodigal=Reporter_options.py_out)
            Reporter_StORFs = StORF_Reported(StORF_options, Contigs)
            #sequence_id, all_StORFs = StORF_Reported(URs, StORF_options)
            StORF_Filler(StORF_options, Reporter_options, Reporter_StORFs)  # Append StORFs to current GFF file from provided genome annotation
            if Reporter_options.verbose == True:
                print("Finished: " + fasta) # Will add number of additional StORFs here

    else:
        parser.error('Incompatible user-arguments selected.')





if __name__ == "__main__":
    main()
    print("Complete")


