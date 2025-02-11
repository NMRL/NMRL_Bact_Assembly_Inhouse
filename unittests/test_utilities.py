import unittest, pandas as pd, os, uuid
from shutil import rmtree
from subscripts.ardetype_utilities import Ardetype_housekeeper as hk
from dateutil.relativedelta import relativedelta
from datetime import datetime


class test_housekeeper(unittest.TestCase):
    '''Testing methods of the housekeeper class'''


    #############################################################
    
    # Pre-testing configurations
    
    #############################################################


    # Methods used to verify dataframe equality based on https://stackoverflow.com/questions/38839402/how-to-use-assert-frame-equal-in-unittest
    def assertDataframeEqual(self, a, b, msg):
        try:
            pd.testing.assert_frame_equal(a, b)
        except AssertionError as e:
            raise self.failureException(msg) from e


    def setUp(self):
        self.addTypeEqualityFunc(pd.DataFrame, self.assertDataframeEqual)


    @staticmethod
    def create_nested_dir_struct(branch_count:int=3, leave_count:int=3, file_count:int=1, root_name:str='top', file_multiplicity:int=1, silent:bool=True) -> list:
        '''
        Method is used to create nested folders with files to be used in testing process.
        The folder tree will have height of 3, which cannot be changed.
        root_name defines the name of the top-most folder
        branch_count - number of non-leave folders (containing subfolders)
        leave_count - number of leave folders (with no subfolders)
        file_count - number of files stored at each level
        file_multiplicity - option to simulate files that have names that differ only by some suffix (e.g. paired fastq)
        Returns list of sample ids and list of file path in order
        '''
        sids = []
        fpaths = []
        for i in range(branch_count):
            for j in range(leave_count):
                os.makedirs(f'./{root_name}/middle{i+1}/bottom{j+1}', exist_ok=True)
                for _ in range(file_count):
                    fname = str(uuid.uuid4())
                    if file_multiplicity <=1:
                        open(f'./{root_name}/middle{i+1}/bottom{j+1}/{fname}.fasta','a').close()
                        if not silent:
                            sids.append(fname)
                            fpaths.append(os.path.abspath(f'./{root_name}/middle{i+1}/bottom{j+1}/{fname}.fasta'))
                    else:
                        for k in range(file_multiplicity):
                            open(f'./{root_name}/middle{i+1}/bottom{j+1}/{fname}_R{k+1}_001.fastq.gz','a').close()
                            if not silent:
                                sids.append(fname)
                                fpaths.append(os.path.abspath(f'./{root_name}/middle{i+1}/bottom{j+1}/{fname}_R{k+1}_001.fastq.gz'))
        if not silent:
            return sids, fpaths


    @staticmethod
    def create_test_file(path_to_file:str='./unittest_file', content:str=""):
        with open(path_to_file, 'w+') as f:
            f.write(content)

    #############################################################
    
    # Tests for methods that do not interact with the file system
    
    #############################################################


    def test_edit_nested_dict(self):
        test = {
            'Valid case':[{'level_1':{'level_2':{'level_3':1}}}, 'level_3', 0, 0],
            'Missing parameter':[{'level_1':{'level_2':{'level_3':1}}}, 'level_4', 0, None],
            'Exception|Wrong nested iterable format':[[], '', '', AttributeError],
            'Exception|Wrong attribute format':[{}, ['XYZ'], '', TypeError]
        }
        for case in test:
            if 'Exception' not in case:
                self.assertEqual(hk.edit_nested_dict(test[case][0],test[case][1],test[case][2]),test[case][3])
            else:
                with self.assertRaises(test[case][3]):
                    hk.edit_nested_dict(test[case][0],test[case][1],test[case][2])

    
    def test_find_in_nested_dict(self):
        test = {
            'Valid case':[{'level_1':{'level_2':{'level_3':1}, 'level_21':2}}, ['level_1','level_2', 'level_3'], 1],
            'Exception|Missing key in sequence':[{'level_1':{'level_2':{'level_3':1}}}, ['level_1','level_21'], LookupError],
            'Exception|Non-dict value accessed before the end of the key sequence':[{'level_1':{'level_2': 1}}, ['level_1','level_2', 'level_3'], LookupError],
            'Exception|Wrong sequence format':[{}, 'XYZ', TypeError],
            'Exception|Wrong nested iterable format':[[], ['XYZ'], TypeError]
        }
        for case in test:
            if 'Exception' not in case:
                self.assertEqual(hk.find_in_nested_dict(test[case][0],test[case][1]), test[case][2])
            else:
                with self.assertRaises(test[case][2]):
                    hk.find_in_nested_dict(test[case][0],test[case][1])


    def test_get_all_keys(self):
        test = {
            'Valid case':[{'level_1':{'level_2':{'level_3':1}, 'level_21':2}}, {'level_1', 'level_2','level_3','level_21'}],
            'Exception|Non-dictionary input':[{'level_1', 'level_2','level_3','level_21'}, AttributeError],
        }
        for case in test:
            if 'Exception' not in case:
                self.assertEqual(hk.get_all_keys(test[case][0]), test[case][1])
            else:
                with self.assertRaises(test[case][1]):
                    hk.get_all_keys(test[case][0])


    def test_map_new_column(self):
        test = {
            'Valid case':[
                pd.DataFrame.from_dict({'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)]}),
                dict(zip([i+1 for i in range(5)],[10+i+1 for i in range(5)])), 
                'id', 
                'var3',
                pd.DataFrame.from_dict({'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)], 'var3':[10+i+1 for i in range(5)]})
                ],
            'Exception|No key column found in dataframe':[
                pd.DataFrame.from_dict({'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)]}),
                dict(zip([i+1 for i in range(5)],[10+i+1 for i in range(5)])),
                'id_column',
                'var3',
                KeyError
                ],
            'Exception|No correspondance between ids used in new column and key column content':[
                pd.DataFrame.from_dict({'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)]}),
                dict(zip([i+1 for i in range(6,10)],[10+i+1 for i in range(5)])),
                'id', 
                'var3',
                KeyError
                ],
            'Exception|Non-dataframe ss_df input':[
                {'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)]},
                dict(zip([i+1 for i in range(5)],[10+i+1 for i in range(5)])), 
                'id', 
                'var3',
                TypeError
                ],
            'Exception|Non-dictionary info_dict input':[
                pd.DataFrame.from_dict({'id':[i+1 for i in range(5)], 'var1':[10 for _ in range(5)], 'var2':[10-i-1 for i in range(5)]}),
                tuple(zip([i+1 for i in range(5)],[10+i+1 for i in range(5)])), 
                'id', 
                'var3',
                TypeError
                ],
        }

        for case in test:
            if 'Exception' not in case:
                self.assertEqual(hk.map_new_column(test[case][0],test[case][1], test[case][2], test[case][3]), test[case][4])
            else:
                with self.assertRaises(test[case][4]):
                    hk.map_new_column(test[case][0],test[case][1], test[case][2], test[case][3])


    #############################################################
    
    # Tests for methods that DO interact with the file system
    
    #############################################################


    def test_asign_perm_rec(self):
        root_name='./top/'
        test_housekeeper.create_nested_dir_struct(root_name=root_name)
        drs, fls = [], []
        for root, dirs, files in os.walk(root_name):
            [drs.append(os.path.join(root,dr)) for dr in dirs]
            [fls.append(os.path.join(root,fl)) for fl in files]
        drs.append(root_name)

        try:
            #Default permissions
            hk.asign_perm_rec(root_name)
            self.assertTrue(all([oct(os.stat(dr).st_mode)[-3:]=='775' for dr in drs]))
            self.assertTrue(all([oct(os.stat(fl).st_mode)[-3:]=='775' for fl in fls]))

            #Different permissions
            hk.asign_perm_rec(root_name,'777')
            self.assertFalse(all([oct(os.stat(dr).st_mode)[-3:]=='775' for dr in drs]))
            self.assertFalse(all([oct(os.stat(fl).st_mode)[-3:]=='775' for fl in fls]))
            
            #Cleanup
            rmtree(root_name)
        except AssertionError as e:
            rmtree(root_name)
            raise e

    
    def test_check_file_existance(self):
        root_name='./top/'
        #Existing files
        test_housekeeper.create_nested_dir_struct(root_name=root_name)
        fls = []
        for root, _, files in os.walk(root_name):
            [fls.append(os.path.join(root,fl)) for fl in files]
        try:
            self.assertTrue(all(list(hk.check_file_existance(fls).values())))
        except AssertionError as e:
            rmtree(root_name)
            raise e

        #Non-existing files
        fls = [str(uuid.uuid4()) for _ in range(10)]
        self.assertTrue(not any(hk.check_file_existance(fls).values()))

        

    
    def test_create_sample_sheet(self):
        root_name = './top/'
        #Fasta
        sids, fpaths = test_housekeeper.create_nested_dir_struct(file_count=3, silent=False,root_name=root_name)
        true = pd.DataFrame.from_dict({'sample_id':sids,'fa':fpaths})
        result = hk.create_sample_sheet(fpaths,mode=1, generic_str='.fasta')
        try:
            self.assertEqual(result, true)
            rmtree(root_name)
        except AssertionError as e:
            rmtree(root_name)
            raise e

        #Fastq
        sids, fpaths = test_housekeeper.create_nested_dir_struct(file_count=3, file_multiplicity=2, silent=False,root_name=root_name)
        ids = []
        rones, rtwos = [], []
        for i,path in enumerate(fpaths):
            if 'R1' in path:
                rones.append(path)
                ids.append(sids[i])
            elif 'R2' in path:
                rtwos.append(path)
        true = pd.DataFrame.from_dict({'sample_id':ids,'fq1':rones,'fq2':rtwos}).sort_values(by='sample_id').reset_index(drop=True)
        result = hk.create_sample_sheet(fpaths, generic_str=r'_R[1,2]_001.fastq.gz').sort_values(by='sample_id').reset_index(drop=True)
        try:
            self.assertEqual(result, true)
            rmtree(root_name)
        except AssertionError as e:
            rmtree(root_name)
            raise e

    
    def test_extract_log_id(self):

        fname = './unittest_file'
        log_content = '''
        Building DAG of jobs...
        Falling back to greedy scheduler because no default solver is found for pulp (you have to install either coincbc or glpk).
        Using shell: /usr/bin/bash
        Provided cores: 4
        Rules claiming more threads will be scaled down.
        Select jobs to execute...

        [Fri Oct 28 15:10:13 2022]
        rule amrfinderplus:
            input: /mnt/home/groups/nmrl/image_files/hamronization_latest.sif, /home/groups/nmrl/image_files/ncbi-amrfinderplus_latest.sif, /mnt/home/groups/nmrl/bact_analysis/Ardetype/data/22_1_4_00420_S25_contigs.fasta
            output: /mnt/home/groups/nmrl/bact_analysis/Ardetype/2022-08-31-nmrl-dnap-pe150-NDX550703_RUO_0047_AHLNV5BGXM/22_1_4_00420_S25_amrfinderplus.tab, /mnt/home/groups/nmrl/bact_analysis/Ardetype/2022-08-31-nmrl-dnap-pe150-NDX550703_RUO_0047_AHLNV5BGXM/22_1_4_00420_S25_amrfinderplus.hamr.tab
            jobid: 0
            wildcards: sample_id_pattern=22_1_4_00420_S25
            resources: mem_mb=1107, disk_mb=1107, tmpdir=/tmp

        [Fri Oct 28 15:11:11 2022]
        Finished job 0.
        1 of 1 steps (100%) done
        '''

        #Valid id in file
        test_housekeeper.create_test_file(content=log_content)
        self.assertEqual(hk.extract_log_id(fname), '22_1_4_00420_S25')
        os.remove(fname)

        #No id in file
        test_housekeeper.create_test_file(content='')
        try:
            self.assertFalse(hk.extract_log_id(fname))
            os.remove(fname)
        except AssertionError as e:
            os.remove(fname)
            raise e


    def test_find_job_logs(self):

        pipe_name = 'unittest_pipe'
        job_logs = './unittest_pipe_job_logs'

        #Fresh logs present
        os.mkdir(job_logs, mode=int('775',8))
        all_logs = []
        logs_to_skip = []
        for i in range(10):
            fname = str(uuid.uuid4())
            open(f'{job_logs}/{fname}', 'a').close()
            all_logs.append(os.path.abspath(f'{job_logs}/{fname}'))
            if i >=5: logs_to_skip.append(os.path.abspath(f'{job_logs}/{fname}'))
        unique = (path for path in set(set(all_logs) - set(logs_to_skip)))
        count = 5

        result, log_count = hk.find_job_logs(pipe_name, logs_to_skip)
        try:
            self.assertListEqual(sorted([e for e in unique]), sorted([e for e in result]))
            self.assertEqual(count, log_count)
        except AssertionError as e:
            rmtree(job_logs)
            raise e


        #Fresh logs missing
        result, log_count = hk.find_job_logs(pipe_name, all_logs)
        try:
            self.assertListEqual([], result)
            self.assertEqual(0, log_count)
            rmtree(job_logs)
        except AssertionError as e:
            rmtree(job_logs)
            raise e
        

    def test_filter_contigs_length(self):
        test = {
            'valid':
                [
                    '>SEQ1\nGCGAATCGAC\n>SEQ2\nGTCGATTCGC',
                    '>SEQ1\nGCGAATCGAC\n>SEQ2\nGTCGATTCGC\n'
                ],
            'valid_short':
                [
                    '>SEQ1\nGCGAATCGAC\n>SEQ2\nC',
                    '>SEQ1\nGCGAATCGAC\n'
                ],
            'all_short':
                [
                    '>SEQ1\nG\n>SEQ2\nC\n',''],
            'Exception|invalid_format':
                ['ABCDEFGHIJKLMNOPQRSTUWXYZ']
            }
        for case in test:
            contigs = './contigs.fasta'
            test_housekeeper.create_test_file(contigs, content=test[case][0])
            if 'Exception' not in case:
                try:
                    hk.filter_contigs_length(contigs,contigs, minlen=2)
                    with open(contigs, 'r+') as f:
                        data = f.read()
                    self.assertEqual(data, test[case][1])
                except Exception as e:
                    os.remove(contigs)
                    raise e
            else:
                try:
                    hk.filter_contigs_length(contigs,contigs, minlen=2)
                    os.remove(contigs)
                    raise AssertionError('Succesful parsing of non-fasta file')
                except Exception as e:
                    os.remove(contigs)
                    self.assertTrue(isinstance(e,ValueError))

    
    def test_parse_folder(self):

        #not a folder
        notfolder='./folder.file'
        nonexfolder='./folder_name'
        test_housekeeper.create_test_file(notfolder)
        with self.assertRaises(ValueError):
            hk.parse_folder(nonexfolder, '')
        try:
            hk.parse_folder(notfolder,'')
            os.remove(notfolder)
            raise AssertionError('Succesful parsing of file as folder')
        except Exception as e:
            os.remove(notfolder)
            self.assertTrue(isinstance(e, ValueError))


        #no files in folders
        root_name='./top'
        test_housekeeper.create_nested_dir_struct(file_count=0, root_name=root_name)

        try:
            self.assertFalse(hk.parse_folder(root_name,''))
            rmtree(root_name)
        except Exception as e:
            rmtree(root_name)
            raise e


        #files found in folders, no substrings, no regex
        _, apaths = test_housekeeper.create_nested_dir_struct(file_count=3,root_name=root_name, silent=False)
        try:
            self.assertListEqual(sorted(apaths),sorted(hk.parse_folder(root_name, file_fmt_str='fasta')))
            rmtree(root_name)
        except Exception as e:
            rmtree(root_name)
            raise e


        #files in folders, substrings, no regex
        test_housekeeper.create_nested_dir_struct(file_count=3,root_name=root_name)
        _, fpaths = test_housekeeper.create_nested_dir_struct(file_count=3, file_multiplicity=2, root_name=root_name, silent=False)
        try:
            self.assertListEqual(sorted(fpaths), sorted(hk.parse_folder(root_name, file_fmt_str='', substr_lst=['.fasta'])))
            rmtree(root_name)
        except Exception as e:
            rmtree(root_name)
            raise e


        #files in folders, regex, no substrings
        _, apaths = test_housekeeper.create_nested_dir_struct(file_count=3,root_name=root_name, silent=False)
        test_housekeeper.create_nested_dir_struct(file_count=3, file_multiplicity=2, root_name=root_name)
        try:
            self.assertListEqual(sorted(apaths), sorted(hk.parse_folder(root_name, file_fmt_str='', regstr_lst=['.*\.fastq\.gz'])))
            rmtree(root_name)
        except Exception as e:
            rmtree(root_name)
            raise e


        #files in folders, regex, substrings
        test_housekeeper.create_nested_dir_struct(file_count=3,root_name=root_name)
        test_housekeeper.create_nested_dir_struct(file_count=3, file_multiplicity=2, root_name=root_name)
        try:
            self.assertFalse(hk.parse_folder(root_name, file_fmt_str='', substr_lst=['.fasta'], regstr_lst=['.*\.fastq\.gz']))
            rmtree(root_name)
        except Exception as e:
            rmtree(root_name)
            raise e

    
    def test_parse_snakemake_log(self):
        log_name = './snakemake_log_test'
        
        test = {'valid':
'''Building DAG of jobs...
Falling back to greedy scheduler because no default solver is found for pulp (you have to install either coincbc or glpk).
Using shell: /usr/bin/bash
Provided cores: 4
Rules claiming more threads will be scaled down.
Select jobs to execute...

[Fri Oct 28 15:10:13 2022]
rule amrfinderplus:
    input: 
    output:
    jobid: 0
    wildcards: sample_id_pattern=test_name
    resources: mem_mb=1107, disk_mb=1107, tmpdir=/tmp
[Fri Oct 28 15:11:11 2022]
Finished job 0.
1 of 1 steps (100%) done''',

        'Exception':
'Not a log file',

        'failed':
'''Building DAG of jobs...
Falling back to greedy scheduler because no default solver is found for pulp (you have to install either coincbc or glpk).
Using shell: /usr/bin/bash
Provided cores: 5
Rules claiming more threads will be scaled down.
Select jobs to execute...

[Fri Oct 28 20:33:42 2022]
rule amrpp:
    input: a
    output: b
    jobid: 0
    wildcards: sample_id_pattern=c
    resources: mem_mb=1000, disk_mb=1000, tmpdir=/tmp

[Fri Oct 28 20:34:08 2022]
Error in rule amrpp:
    jobid: 0
    output: b

Shutting down, this might take some time.
Exiting because a job execution failed. Look above for error message
'''
        }
        for case in test:
            test_housekeeper.create_test_file(log_name, content = test[case])
            df = hk.parse_snakemake_log(log_name)
            try:
                if 'failed' in case:
                    time_sec_total = relativedelta(datetime.fromtimestamp(os.path.getctime(log_name)), datetime.strptime('2022:10:28-20:33:42', '%Y:%m:%d-%H:%M:%S'))
                    time_sec_total = time_sec_total.hours*3600+time_sec_total.minutes*60+time_sec_total.seconds
                    self.assertEqual(df,pd.DataFrame({
                        "log_path":[log_name],
                        "job_name":['amrpp'],
                        "sample_id":['c'],
                        "is_failed":[1],
                        "mem_gb_snakemake":[1000/1024],
                        "cpu_snakemake":[1],
                        "mem_gb_req":[37500/1024],
                        "time_sec_req":[23400],
                        "start_time":['2022:10:28-20:33:42'],
                        "time_sec_total":[time_sec_total],
                        "Eff":[round(100*time_sec_total/23400,2)]
                    }))
                elif 'valid' in case:

                    self.assertEqual(df,pd.DataFrame({
                        "log_path":[log_name],
                        "job_name":['amrfinderplus'],
                        "sample_id":['test_name'],
                        "is_failed":[0],
                        "mem_gb_snakemake":[1107/1024],
                        "cpu_snakemake":[1],
                        "mem_gb_req":[12000/1024],
                        "time_sec_req":[1800],
                        "start_time":['2022:10:28-15:10:13'],
                        "time_sec_total":[58],
                        "Eff":[round(100*58/1800,2)]
                    }))
                elif 'Exception' in case:
                    self.assertEqual(df,pd.DataFrame())
                os.remove(log_name)
            except Exception as e:
                os.remove(log_name)
                raise e


    # def test_read_json_dict(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_read_yaml(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_remove_old_files(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception

    # def test_rename_file(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_update_log_history(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_update_log_summary(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_validate_yaml(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_write_json(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


    # def test_write_yaml(self):
    #     test = {
    #         'Valid input':[],
    #         'Exception|':[]
    #     }
    #     for case in test:
    #         if 'Exception' not in case:
    #             self.assertEqual(1,1)
    #         else:
    #             with self.assertRaises(Exception):
    #                 raise Exception


if __name__ == "__main__":
    unittest.main()