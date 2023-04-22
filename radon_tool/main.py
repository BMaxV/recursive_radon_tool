from radon.complexity import cc_rank, cc_visit
import matplotlib.pyplot as plt
import os
import jinja2

import importlib.resources as pkg_resources
from . import templates

import argparse


# import matplotlib

# font = {
# 'family' : 'normal',
# 'weight' : 'bold',
# 'size'   : 22}
# matplotlib.rc("font",**font)

def analyse_my_files(rootpath=None,skip_errors=True):
    assert "home" in os.getcwd()
    
    mylist = os.listdir()
    path = os.getcwd()
    
    if rootpath == None:
        rootpath = path

    d = {}
    sub_d = {}
    rpl = len(rootpath)
    
    for maybe_file in mylist:
        
        if os.path.isdir(maybe_file) and not os.path.islink(maybe_file):
            
            if maybe_file in ["build","built","docs","dist","tests","deps"]:
                continue
            
            try:
                old=os.getcwd()
                os.chdir(maybe_file)
                r = analyse_my_files(rootpath,skip_errors=skip_errors)
                os.chdir(old)
            except RecursionError:
                r = {}
            
            
            if len(r) == 0:
                continue
            #wtf.
            collected={}
            for key in r:
                if ".py" in key:
                    for cat_key in r[key]:
                        if cat_key not in collected:
                            collected[cat_key]=0
                        collected[cat_key]+=r[key][cat_key]
                
                if key in ["A","B","C","D","E","F"]:
                    if key not in collected:
                        collected[key]=0
                    collected[key]+=r[key]
                
            for key in collected:
                if key in ["A","B","C","D","E","F"]:
                    if key not in d:
                        d[key]=0
                    d[key]+= collected[key]
                
            d[maybe_file] = r
           
           
        elif ".py" in maybe_file:
            try:
                r = analyse_file(maybe_file)
                if r != None:
                    d[maybe_file] = r
            except:
                print("error parsing",maybe_file)
                print(os.getcwd())
                if not skip_errors:
                    raise
            
    
    return d


def analyse_file(fn):
    
    if fn[-3:] != ".py":
        return
    
    with open(fn, "r") as f:
        t = f.read()
    r = cc_visit(t)
    bins = {}
    worst = 0
    worst_f = None
    for function in r:
        if function.complexity > worst:
            worst = function.complexity
            worst_f = function
        this_rank = cc_rank(function.complexity)

        if this_rank not in bins:
            bins[this_rank] = 1
        else:
            bins[this_rank] += 1

    # print(fn, bins)
    # print("worst",worst,worst_f)

    return bins


def recursive_plot_output_all(my_dict, this_level_fn=None):
    path = os.getcwd()
    render_file_names = []
    
    temp_d = {}
    links =[]
    for filepath in my_dict:
        filedata = my_dict[filepath]
        
        if ".py" in filepath:
            if len(filedata)==0:
                continue
            nfn = str(filepath).split(".")[0]
            real_fn = plot_output_single(filedata, output_name=str(nfn))
            render_file_names.append(real_fn)
            
        else:
            
            # this is where we go deeper.
            if type(filedata)==dict:
                if len(filedata)==0:
                    continue
                new_sub_folder="output_"+filepath
                old_path = os.getcwd()
                try:
                    try:
                        os.mkdir(new_sub_folder)
                    except FileExistsError:
                        pass
                except PermissionError:
                    print("new_sub_folder",new_sub_folder)
                    print(os.getcwd())
                    raise
                os.chdir(new_sub_folder)
                recursive_plot_output_all(my_dict[filepath], this_level_fn=filepath)
                os.chdir(old_path)
                links.append(filepath)
            
            # we're not in the results, we're just counting.
            else:
                key = filepath
                if key not in temp_d:
                    temp_d[key] = 0
                temp_d[key] += my_dict[key]
    
    if temp_d !={}:
        real_fn = plot_output_single(temp_d, output_name="summed_deeper_levels")
        render_file_names.append(real_fn)
    
    create_html(render_file_names, links, this_level_fn)
    
    return render_file_names


def count_all(d):
    # everything in {"anem":key}
    # is either a dict or a number.
    # if it's a number I want to count it, if it's a
    # dict, I want to go deeper.
    # actually, i want to separate the two first.
    # then go through all deeper levels first
    # then count.
    a = 1


def plot_output_single(bins,  output_name="output"):

    mylabels = []
    real_labels = []
    slices = []
    for rank in bins:
        mylabels.append((rank, bins[rank]))

    # sort by category, not number to keep coloring consistent.
    mylabels.sort(key=lambda x: x[0])

    for rank in mylabels:
        slices.append(bins[rank[0]])
        real_labels.append(rank[0]+":"+str(rank[1]))
    
    plt.pie(slices, labels=real_labels)
    plt.title(output_name)
    nfn = "radonpie" + output_name + ".svg"
    plt.legend()
    plt.savefig(nfn)
    plt.clf()

    return nfn


def rprint(d, level=0):
    for key in d:
        if type(d[key]) == dict:
            print(" "*level, key)
            rprint(d[key], level+1)
        else:
            print(" "*level, key, d[key])

def resort_info_boxes(r2):
    newl = []
    new_rows = []
    while len(r2) > 0:
        c = 0
        m = 4
        new_l = []
        while c < m and len(r2) > 0:
            el = r2.pop(0)
            new_l.append(el)
            c += 1
        new_rows.append(new_l)
        
    return new_rows

def create_html(render_file_names, links, this_level_fn):

    new_rows = resort_info_boxes(render_file_names)
    
    data = {"plotfiles": new_rows, 
            "links": links,
            "this_level_fn": this_level_fn}
   
    my_temp = pkg_resources.read_text(templates, "template.html")
    T = jinja2.Template(my_temp)
    
    text = T.render(data)
    with open("output.html", "w") as f:
        f.write(text)

def main(make_output=True, skip_errors=True):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dontskiperrors", 
    action='store_const', const=True,
    help="disable skipping over problems, to trigger the stacktrace and take a look what's causing the problem.")
    
    args=parser.parse_args()
    #parser.add_argument("--skip-errors", help="increase output verbosity")
    if args.dontskiperrors:
        skip_errors=False
    print("\n\n\n",[args],"\n\n\n")
    r = analyse_my_files(skip_errors=skip_errors)
    
    try:
        os.mkdir("radon_tool_output")
    except FileExistsError:
        pass
    os.chdir("radon_tool_output")
    if make_output:
        recursive_plot_output_all(r)


if __name__ == "__main__":
    
    main()
