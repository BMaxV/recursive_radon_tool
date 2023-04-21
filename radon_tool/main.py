from radon.complexity import cc_rank, cc_visit
import matplotlib.pyplot as plt
import os
import jinja2
import importlib.resources as pkg_resources

from . import templates

# import matplotlib

# font = {
# 'family' : 'normal',
# 'weight' : 'bold',
# 'size'   : 22}
# matplotlib.rc("font",**font)


def analyse_my_files(paths=None, rootpath=None):
    mylist = os.listdir()

    path = os.getcwd()

    if rootpath == None:
        rootpath = path

    d = {}
    paths = {}
    sub_d = {}
    rpl = len(rootpath)
    relative_path = path[rpl:]

    paths[path] = relative_path

    for maybe_file in mylist:
        if os.path.isdir(maybe_file):
            os.chdir(maybe_file)
            r, paths = analyse_my_files(paths, rootpath)
            os.chdir("..")
            
            if len(r) == 0:
                continue
            print("analysed",maybe_file,r)
            d[maybe_file] = r
            paths[maybe_file] = paths

        else:
            r = analyse_file(maybe_file)
            if r != None:
                d[maybe_file] = r

    return d, paths


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


def recursive_plot_output_all(my_dict, paths, previouslevelfn=None, folders=True, files=True):
    render_file_names = []
    project_file_path = "."
    temp_d = {}
    
    for filepath in my_dict:
        if ".py" in filepath:
            continue
        
        new_sub_folder = "output_"+filepath
        print("trying to make", new_sub_folder)
        
        try:
            os.mkdir(new_sub_folder)
        except FileExistsError:
            pass
        
        old_path = os.getcwd()
        links = []
        

        for filename in my_dict[filepath]:
            filedata = my_dict[filepath][filename]
            
            if len(filedata)==0:
                continue
                
            if files and  ".py" in filename:
                nfn = str(filename).split(".")[0]
                real_fn = plot_output_single(
                    filedata, filepath, output_name=str(nfn))

                sub_d = {"name":filename, "filename": real_fn}
                render_file_names.append(sub_d)
            
            for key in filedata:
                if type(filedata[key])!=dict:
                    if key not in temp_d:
                        temp_d[key] = 0
                    temp_d[key] += filedata[key]

            if not ".py" in filename:
                links.append(filename)

        if folders:
            n = str(filepath)
            
            real_fn = plot_output_single(temp_d, filepath, output_name=n)
            name = filepath.split("/")[-1]
            if real_fn != None:
                sub_d = {"name": name, "filename": real_fn}
                render_file_names.append(sub_d)

        if len(my_dict[filepath]) != 0:

            current = os.getcwd()
            
            os.chdir(new_sub_folder)
            create_html(render_file_names, links, previouslevelfn)
            recursive_plot_output_all(
                my_dict[filepath], paths, previouslevelfn="output.html", folders=folders, files=files)
            os.chdir(current)
            
        os.chdir(old_path)

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


def plot_output_single(bins, filepath, output_name="output"):

    if len(bins) == 0:
        return None

    new_sub_folder = "output_"+filepath.split("/")[-1]
    
    try:
        os.mkdir(new_sub_folder)
    except FileExistsError:
        pass
    old_path = os.getcwd()

    os.chdir(new_sub_folder)

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
    print(slices)
    plt.pie(slices, labels=real_labels)
    
    nfn = "radonpie" + output_name + ".svg"
    plt.legend()
    plt.savefig(nfn)
    plt.clf()
    os.chdir(old_path)

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

def create_html(render_file_names, links, previouslevelfn):

    new_rows = resort_info_boxes(render_file_names)

    data = {"plotfiles": new_rows, 
            "links": links,
            "previouslevelfn": previouslevelfn}
   
    my_temp = pkg_resources.read_text(templates, "template.html")
    T = jinja2.Template(my_temp)
    
    text = T.render(data)
    with open("output.html", "w") as f:
        f.write(text)


def main(make_output=True):

    r, paths = analyse_my_files()

    if make_output:
        recursive_plot_output_all(r, paths)


if __name__ == "__main__":
    main()
