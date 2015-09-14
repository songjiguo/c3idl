#------------------------------------------------------------------------------
# pycparser: c-to-c.py
#
# Example of using pycparser.c_generator, serving as a simplistic translator
# from C to AST and back to C.
#
# Copyright (C) 2008-2015, Eli Bendersky
# License: BSD
#------------------------------------------------------------------------------
from __future__ import print_function
from pycparser import parse_file, preprocess_file
from pycparser import c_parser, c_ast, c_generator, c_parser, c_generator
from pprint import pprint

import keywords
import subprocess

class MyCode():
    def __init__(self):
        self.ifcode = {}
        
    def add_interface(self, if_name):
        self.ifcode[if_name] = InterfaceCode(if_name)

class InterfaceCode(object):
    def __init__(self, interface_name):
        self.blocks = {}
        self.name   = interface_name
    
    def add_block(self, block_name):
        self.blocks[block_name] = BlockCode(block_name)

class BlockCode(object):
    def __init__(self, block_name):
        self.rules = []
        self.name   = block_name
        self.block_code = ""
        
    def gen_code(self, arg1, *args):   # pass the conditions in
        #print ("Python does not support function overloading")
        #self.set_name(arg1)
        
        if args:
            #for item in args:
            #    print (item)
            self.block_code = "hello world" 
        else:
            print (arg1)
            
    def set_name(self, block_name):
        name = block_name

    def show_code(self):
        print (self.block_code)  
        
#===============================================================================
#  block is in the form of (predicate, code, blk name)
#  gdescp is in the form of ['desc_close_itself', 'desc_global_global', ...]
#  fdescp is in the form of [function name, normalPara, sm_state, idlRet, idlPara]
#
#  This is the evaluation function and return the code for a match
#===============================================================================   
def condition_eval(block, (gdescp, fdescp)):
    #print ("\n <<<<<<< eval starts! >>>>>>>>")
    IFCode = ""
    IFBlkName = ""
    
    list_descp = list(traverse(gdescp)) + list(traverse(fdescp))
    #print ("list descp ->") 
    #print (list_descp)
    #print ("<- list descp") 
    
    find_any = False
    
    for blk in block.list:
        list_blks = []
        __list_blks = list(traverse(blk[0]))
        for item in __list_blks:
            list_blks.append(item) 
        #print ("\na ist of blks: sz --> ", len(list_blks))
        #print (blk[0])
        #print (blk[1])
        #print (list_blks)
        
        match = 0;
        for pred in list_blks:
            pred = pred.split('|')
            #print ("a pred: --> ")
            #print (pred)
            #print (list_descp)
            for desc in list_descp:
                if (desc in pred):
                    match = match + 1;
        if (match == len(list_blks)):
            #print ("found a match")
            IFCode = blk[1] + block.list[-1][1]   # last(pred, code) -- [-1][1] is for function pointer
            IFBlkName = blk[2]  
            
            find_any = True
            break;  # stop once we have found a match TODO: check the consistency

    if (find_any is False):
        for blk in block.list:
            if (blk[0][0] == "no match"):
                return (blk[0][0], blk[1])
                #print(blk[0])
                #print(blk[1])
                #print(blk[2])
    #===========================================================================
    # if (find_any is False):
    #     print ("can not find any for this func block")
    #     print (block.list[0])
    #     for blk in block.list:
    #         #print (blk[0])
    #         if (blk[0] == "no match"):
    #             print(blk[1])
    #             print(blk[2])
    #===========================================================================

    return (IFBlkName, IFCode)
    #print ("<<<<<<< eval ends! >>>>>>>>\n")
        
def traverse(o, tree_types=(list, tuple)):
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value, tree_types):
                yield subvalue
    else:
        yield o

# fdesc[0] is the func name, fdesc[1] is the normal pars
# fdesc[4] is the IDL-ed pars  
def replace_params(fdesc, code):
    name    = fdesc[0]
    params  = fdesc[1]
    #pprint (result.tuple[0].functions[0].info)
    #print (name)
    #print(fdesc[4])
    
    parent_id = ""
    id = ""
    tmp_list = list(traverse(fdesc[4]))
    for item in tmp_list:
        if (item == "desc_lookup" or item == "desc_data_remove"):
            id = tmp_list[tmp_list.index(item)+2]
        if (item == "parent_desc"):
            parent_id = tmp_list[tmp_list.index(item)+2]
    #print (id)
    #print (parent_id)
    
    param_list = []
    paramdecl_list = []
    for para in params:               # fdesc[1] is the list of normal parameters
        param_list.append(para[1])      # para[0] is the type, para[1] is the value
        paramdecl_list.append(para[0]+" "+para[1])  # this is for the parametes used in the function decl
    code = code.replace("IDL_params", ', '.join(param_list))
    code = code.replace("IDL_pars_len", str(len(param_list)))
    code = code.replace("IDL_parsdecl", ', '.join(paramdecl_list))
    code = code.replace("IDL_fname", name)
   
    code =  code.replace("IDL_id", id)
    code =  code.replace("IDL_parent_id", parent_id)
    
    return code        

########################
# generating functions
########################
def generate_globalvas(result, IFcode):
    cmd = 'sed -nr \"/\<client header start\>/{:a;n;/'\
          '\<client header end\>/b;p;ba} \" pred\_code\/code.c'
    p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    code, err = p.communicate()
    #print (code.split())
    #pprint(result.gvars["desc_data"])  
      
    # desc_track
    tmp = "\n" + code.split()[0] + " " + code.split()[1] + " { \n"
    for item in result.gvars["desc_data"]:
        tmp = tmp + "    " + item + ";\n"
    tmp = tmp + "\n};\n"  
    code = code.replace("struct IDL_desc_track\n", tmp) # only replace a line, not everywhere
    code = code.replace("struct IDL_desc_track", "struct desc_track") # only replace a line, not everywhere

    # all fields of desc_track 
    tmp = ""
    for item in result.gvars["desc_data"]:
        tmp = tmp + item + ", "
    code = code.replace("IDL_desc_track_fields", tmp[:-2])
    
    # header files
    code = r'''#include "../cidl_gen.h"''' + "\n" + code 
    
    #print (code)  
    IFcode["header"] = code  

# the function pointer decl blocks    
def generate_fnptr(funcblocks, globalblocks, IFcode):
    __IFcode = {}        
    for fblk in funcblocks:
        #fblk.show()
        for item in fblk.list:
            if (item[0] and item[0][0] == 'fnptr decl'):
                name = item[2]
                code = item[1]
                __IFcode[name] = code
    for gblk in globalblocks:
        #gblk.show()
        for item in gblk.list:
            if (item[0] and item[0][0] == 'fnptr decl'):
                name = item[2]
                code = item[1]
                __IFcode[name] = code
    IFcode["funptr"] = __IFcode

def generate_gblocks(globalblocks, IFDesc, IFcode):
    # the global blocks
    if (globalblocks):
        __IFcode = {}
        for gblk in globalblocks:
            #print (gblk.list)
            name, code= condition_eval(gblk, (IFDesc[0], None))
            if (name and code):    # there should be any params, otherwise it should be function
                __IFcode[name] = code
                # now write out static function declarations!!!
                #print (code.split('\n', 1)[0])
                IFcode["header"] = IFcode["header"] + code.split('\n', 1)[0][:-2]+";" + "\n"
    IFcode["global"] = __IFcode               

def generate_fblocks(result, funcblocks, IFDesc, IFcode):
    
    no_match_code_list = []
    
    # the function blocks    
    for fdesc in IFDesc[1]:
        __IFcode = {}        
        for fblk in funcblocks:
            #fblk.show()

            name, code = condition_eval(fblk, (IFDesc[0], fdesc))  
            code = replace_params(fdesc, code)

            if (name == "no match"):
                if (code not in no_match_code_list):
                    no_match_code_list.append(code)
                continue;
            
            if (name and code):
                __IFcode[name] = code
                # now write out static function declarations!!!
                #print(name)
                #print (code.split('\n', 1)[0])
                IFcode["header"] = IFcode["header"] + code.split('\n', 1)[0][:-2]+";" + "\n"
        #=======================================================================
        # for dname, dcode in __IFcode.iteritems():
        #     if (dname):
        #         print ("<<<<" + dname + ">>>>")
        #         print (dcode)
        #=======================================================================
        IFcode[fdesc[0]] = __IFcode
        
    
    #exit()
    # some post processing (pop up the saved params, find create function etc...)  
    code = IFcode["global"]['BLOCK_CLI_IF_BASIC_ID']
    #code = code.replace("IDL_create_fname", "kevin")
    populated_create_fn_pars = []
    for fdesc in IFDesc[1]:
        #print(fdesc[0]) 
        #print(fdesc[2]) 
        if (fdesc[2] == "create"):
            code = code.replace("IDL_create_fname", fdesc[0])
            #print(fdesc[0]) 
            #print(fdesc[2]) 
            #print (fdesc[1])
            # compare create function par list and the desc saved fileds, then populate
            for saved_field in result.gvars["desc_data"]:
                for create_fn_par in fdesc[1]:
                    #print (' '.join(create_fn_par))
                    #print (saved_field)
                    if (saved_field == ' '.join(create_fn_par)):
                        populated_create_fn_pars.append("desc->"+create_fn_par[1])  # populate the par val

    #print (', '.join(populated_create_fn_pars))
            
    code = code.replace("IDL_desc_saved_params", ', '.join(populated_create_fn_pars))            
    IFcode["global"]['BLOCK_CLI_IF_BASIC_ID'] = code
    
    #pprint (IFcode)    
    #exit()
    
    # this is the non-match list and should be empty static inline function
    #print (no_match_code_list)
    IFcode["header"] = IFcode["header"] + '\n' + ''.join(no_match_code_list)
    #pprint (IFcode)
    #exit()
        

# construct global/function description
def generate_description(result, funcdescps, globaldescp):
    for tup in result.tuple:
        #pprint (tup.info)
        for key, value in tup.info.iteritems():
            if (key is not tup.sm_create and
                key is not tup.sm_mutate and
                key is not tup.sm_terminate):
                globaldescp.append(key+"_"+value)
        for func in tup.functions:
            #print (func.normal_para)  
            normalPara = func.normal_para          
            #pprint (func.info)
            idlRet  = []
            idlPara = []
            for key, value in func.info.iteritems():
                if (key == func.name or key == func.sm_state):
                    continue
                if (value and key is not func.desc_data_retval):
                    idlPara.append((key, value))
                if (value and key is func.desc_data_retval):
                    idlRet.append((key, value))
            #print (tmpRet)
            perFunc = (func.info[func.name], normalPara,    #--- this is the funcdescp tuple
                       func.info[func.sm_state], idlRet, idlPara)
            #pprint (perFunc)
            #print ()
            funcdescps.append(perFunc)  
            
#  construct blocks of (predicate, code) 
def generate_blocks(globalblocks, funcblocks):
    
    # no need to do this anymore
    #===========================================================================
    # # transform the predefine code for further processing (e.g., add "\n")
    # cmd = 'sed -f pred\_code\/convert.sed pred\_code\/code.c > pred\_code\/tmpcode'
    # subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    #===========================================================================
    
    fblk = []
    gblk = []
    
    fblk.append(keywords.block_cli_if_invoke())
    fblk.append(keywords.block_cli_if_invoke_ser_intro())
    fblk.append(keywords.block_cli_if_recover_subtree())
    fblk.append(keywords.block_cli_if_track())  
    fblk.append(keywords.block_cli_if_recover_init())

    gblk.append(keywords.block_cli_if_recover())
    gblk.append(keywords.block_cli_if_basic_id()) 
    gblk.append(keywords.block_cli_if_recover_upcall()) 
    gblk.append(keywords.block_cli_if_recover_data())
    gblk.append(keywords.block_cli_if_save_data())
    gblk.append(keywords.block_cli_if_recover_upcall_entry())  
    
    for item in gblk:
        globalblocks.append(item)          
    for item in fblk:
        funcblocks.append(item)
        
#===============================================================================
# the main functoin to paste and generate the fina code/ast
#===============================================================================
def paste_idl_code(IFcode):
    
    result_code = IFcode['header'] + "\n"

    #===========================================================================
    # tmp_dict = IFcode['funptr']
    # for k, v in tmp_dict.iteritems():
    #     #print(v)
    #     result_code = result_code + v
    # result_code = result_code + "\n"
    #===========================================================================
       
    tmp_dict = IFcode['global']
    for k, v in tmp_dict.iteritems():
        #print(v)        
        result_code = result_code + v
        result_code = result_code + "\n"

    #===========================================================================
    # tmp_dict = IFcode['header']
    # for k, v in tmp_dict.iteritems():
    #     #print(v)        
    #     result_code = result_code + v
    #     result_code = result_code + "\n"
    #===========================================================================
    
    for kname, vdict in IFcode.iteritems():
        if (kname == "funptr" or kname == "global" or kname == "header"):
            continue
        for k, v in vdict.iteritems():
            #print(v)
            result_code = result_code + v
            result_code = result_code + "\n"       
    
    #print (result_code)
    
    
    # make a fake main function for testing only
    fake_main = r"""
/* this is just a fake main function for testing. Remove it later  */
int main()
{
    return 0;
}
"""
    result_code = result_code + "\n" + fake_main

    # write out the result to the file (easier debug)
    output_file = "pred_code/output.c"
    with open(output_file, "w") as text_file:
        text_file.write("{0}".format(result_code))
    
    # generate the new ast for the interface code
    parser = c_parser.CParser()
    ast = parse_file(output_file, use_cpp=True,
                     cpp_path='cpp',
                     cpp_args=r'-Iutils/fake_libc_include')    
    #ast.show()

    print ("IDL process is done")
    
#===============================================================================
# the function to process passed in result and generate block code
#===============================================================================
def idl_generate(result, parsed_ast):

    globaldescp     = []
    funcdescps      = []
    globalblocks    = []
    funcblocks      = []
    IFcode          = {}
    
    IFDesc = (globaldescp, funcdescps)    
    #pprint (result.gvars["desc_data"])

    # update blocks and descriptions to be used for evaluation 
    generate_description(result, funcdescps, globaldescp)    
    generate_blocks(globalblocks, funcblocks)
    
    # evaluate the conditions and generate block code
    generate_globalvas(result, IFcode)
    generate_gblocks(globalblocks, IFDesc, IFcode)
    #generate_fnptr(funcblocks, globalblocks, IFcode)
    generate_fblocks(result, funcblocks, IFDesc, IFcode)

    #pprint (IFcode)
    
    #exit()
    paste_idl_code(IFcode)   # make some further process here
