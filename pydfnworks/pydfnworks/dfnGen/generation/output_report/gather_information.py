"""
    :filename: gather_information.py
    :synopsis: gathers information from files output by dfnGen and combines them into lists of dictionaries for each fracture and fracture families. Additional information about the domain and network are put into a general parameter dictionary.
    :version: 1.0
    :maintainer: Jeffrey Hyman
    .. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
"""

import re
import sys

# from pydfnworks.dfnGen.generation.generator import parse_params_file
from pydfnworks.dfnGen.generation.output_report.helper import load_colors

from pydfnworks.general.logging import local_print_log 

def parse_dfn_output(params, families):
    """ Parses information from the 'DFN_output.txt' report generated by dfnGen into family dictionaries and params dictionary.

    Parameters
    ------------
        params : dictionary
            Output report dictionary containing general parameters. See output_report for more details
        
        families : list
            list of dictionaries with information about fracture family

    Returns
    ---------
        params : dictionary
            Output report dictionary containing general parameters. See output_report for more details
        f
        amilies : list
            list of dictionaries with information about fracture family

    Notes
    -------
        Information for user defined fractures are not included into the family dictionaries


    """

    bulk_params = [
        "Total Surface Area",
        "Total Fractures Volume",
        "Total Fracture Density   (P30)",
        "Total Fracture Intensity (P32)",
        #"Total Fracture Porosity  (P33)",
        "Total Fractures Rejected"
    ]

    final_params = [
        "Isolated Fractures Removed", "Final Number of Fractures",
        "Total Fractures Rejected", "Total Fractures Re-translated"
    ]

    intersection_params = [
        "    Number of Intersections", "    Intersections Shortened",
        "    Original Intersection (Before Intersection Shrinking) Length",
        "    Intersection Length Discarded", "    Final Intersection Length"
    ]

    family_parms = [
        "    Fractures After Isolated Fracture Removal",
        "    Isolated Fractures Removed", "    Accepted", "    Rejected",
        "    Surface Area", "    Volume", "    Fracture Intensity (P32)"
    ]

    string_params = ["Time Stamp"]

    pre_iso_flag = False
    post_iso_flag = False
    family_block_flag = False
    with open('DFN_output.txt', "r") as fp:
        for line in fp.readlines():
            if "Statistics Before Isolated Fractures Removed" in line:
                pre_iso_flag = True
                #print("Pre ISO")
            if "Statistics After Isolated Fractures Removed" in line:
                pre_iso_flag = False
                post_iso_flag = True
                #print("Post ISO")

            if len(line.split()) > 0:
                parsed_line = line.split(": ")
                if len(parsed_line) > 1:
                    variable = parsed_line[0]
                    value = parsed_line[1].rstrip()
                    # Bulk Params
                    if variable in string_params:
                        params[variable] = value

                    if variable in bulk_params:
                        if "m" in value:
                            value = value.split()[0]
                        if pre_iso_flag:
                            params["Pre-Iso " + variable] = float(value)
                        elif post_iso_flag:
                            params["Post-Iso " + variable] = float(value)

                    elif variable in final_params:
                        params[variable] = int(value)

                    elif variable in intersection_params:
                        if "m" in value:
                            value = value.split()[0]
                        params[variable.lstrip()] = float(value)

                    # Parse by Family
                    elif variable == "Family":
                        for fam in families:
                            if int(value) == fam["Global Family"]:
                                family_block_flag = True
                                break

                    elif variable in family_parms and family_block_flag:
                        if "m" in value:
                            value = value.split()[0]
                        if pre_iso_flag:
                            fam["Pre-Iso " + variable.lstrip()] = float(value)
                        elif post_iso_flag:
                            fam["Post-Iso " + variable.lstrip()] = float(value)
                        if variable.lstrip() == "Fracture Intensity (P32)":
                            family_block_flag = False

    return params, families


def get_family_information():
    """ Reads in information from families.dat file that lists the data for each fracture family.

    Parameters
    -----------
        None

    Returns
    --------
        families : list
            List of dictionaries with information about fracture family
    
    Notes
    ------
        None

    """

    int_params = [
        "Rectangular Family", "Global Family", "Number of Vertices",
        "Layer Number", "Region Number", "Ellipse Family"
    ]
    string_params = [
        "Distribution", "Region", "Layer",
        "Beta Distribution (Rotation Around Normal Vector)"
    ]
    families = []
    with open('dfnGen_output/families.dat', "r") as fp:
        family = {}
        for line in fp.readlines():
            if len(line.split()) > 0:
                parsed_line = line.split(": ")
                variable = parsed_line[0]
                value = parsed_line[1].rstrip()
                if variable in string_params:
                    family[variable] = str(value)
                elif variable in int_params:
                    family[variable] = int(value)
                else:
                    family[variable] = float(value)

            else:
                families.append(family)
                del family
                family = {}

    # Add necessary keys for user defined fractures and shapes
    new_families = []
    for family in families:
        keys = family.keys()

        if "UserDefined Rectangle Family" in keys:
            family["Global Family"] = -1
            family["Distribution"] = "user_rectangles"
            family["Layer"] = False
            family["Region"] = False
            family["Shape"] = "Rectangle"

        elif "UserDefined Ellipse Family" in keys:
            family["Distribution"] = "user_ellipses"
            family["Global Family"] = 0
            family["Layer"] = False
            family["Region"] = False
            family["Shape"] = "Ellipse"

        elif "UserDefined Polygon Family" in keys:
            family["Distribution"] = "user_polygons"
            family["Global Family"] = -2
            family["Layer"] = False
            family["Region"] = False
            family["Shape"] = "Polygon"

        elif "Rectangular Family" in keys:
            family["Shape"] = "Rectangle"
            new_families.append(family)

        elif "Ellipse Family" in keys:
            family["Shape"] = "Ellipse"
            new_families.append(family)

    families = new_families
    del new_families

    # Parse Layers and Regions
    for family in families:
        if family["Global Family"] > 0:
            #try:
            if family["Layer"] != "Entire domain":
                values = re.sub("{|}", "", family["Layer"]).strip().split(",")
                family["z_min"] = float(values[0])
                family["z_max"] = float(values[1])
                family["Layer"] = True
            else:
                family["Layer"] = False

            if family["Region"] != "Entire domain":
                values = re.sub("{|}", "", family["Region"]).strip().split(",")
                family["x_min"] = float(values[0])
                family["x_max"] = float(values[1])
                family["y_min"] = float(values[2])
                family["y_max"] = float(values[3])
                family["z_min"] = float(values[4])
                family["z_max"] = float(values[5])
                family["Region"] = True
            else:
                family["Region"] = False
        # except:
        #     print("ERROR on this family")
        #     print(family)
        #     print("Unexpected error:", sys.exc_info()[0])
        #     pass

    num_fam = len(families)
    if num_fam == 1:
        local_print_log(f"--> There is {num_fam} Fracture Family")
    else:
        local_print_log(f"--> There are {num_fam} Fracture Families")

    return families


def create_fracture_dictionary():
    fracture = {
        "frac_id": None,
        "x-radius": None,
        "y-radius": None,
        "normal": [None, None, None],
        "center": {
            "x": None,
            "y": None,
            "z": None
        },
        "family": None,
        #"connections": None,
        "surface_area": None,
        "removed": bool
    }
    return fracture


def get_fracture_information():
    """ Reads in information about fractures. Information is taken from radii.dat, translations.dat, normal_vectors.dat, and surface_area_Final.dat files. Information for each fracture is stored in a dictionary created by create_fracture_dictionary() that includes the fracture id, radius, normal vector, center, family number, surface area, and if the fracture was removed due to being isolated 

    Parameters
    -----------
        None

    Returns
    --------
        fractuers : list
            List of fracture dictionaries with information.
    
    Notes
    ------
        Both fractures in the final network and those removed due to being isolated are included in the list. 

    """
    fractures = []
    accepted_fractures = 0
    # walk through radii file and start parsing fracture information
    with open('dfnGen_output/radii.dat', "r") as fp:
        fp.readline()  # header
        for i, line in enumerate(fp.readlines()):
            fracture = create_fracture_dictionary()

            if "R" in line:
                line = line.split()
                fracture["frac_id"] = -1
                fracture["x-radius"] = float(line[0])
                fracture["y-radius"] = float(line[1])
                fracture["family"] = float(line[2])
                fracture["removed"] = True
            else:
                line = line.split()
                fracture["frac_id"] = i + 1
                fracture["x-radius"] = float(line[0])
                fracture["y-radius"] = float(line[1])
                fracture["family"] = int(line[2])
                fracture["removed"] = False
                accepted_fractures += 1
            fractures.append(fracture)

    # Walk through translation file
    with open('dfnGen_output/translations.dat', "r") as fp:
        fp.readline()  # header
        for i, line in enumerate(fp.readlines()):
            line = line.split()
            fractures[i]["center"]["x"] = float(line[0])
            fractures[i]["center"]["y"] = float(line[1])
            fractures[i]["center"]["z"] = float(line[2])
            if not fractures[i]["removed"] and len(line) > 3:
                error = f"ERROR!!! Unexpected removed fracture in output report.\nCheck fracture number {i+1}\n.Exiting Program.\n"
                sys.stderr.write(error)
                sys.exit(1)

    # Walk through normal vector file
    with open("dfnGen_output/normal_vectors.dat", "r") as fp:
        for i in range(len(fractures)):
            if not fractures[i]["removed"]:
                line = fp.readline().split()
                fractures[i]["normal"][0] = float(line[0])
                fractures[i]["normal"][1] = float(line[1])
                fractures[i]["normal"][2] = float(line[2])

    # Walk through surface_area_file and keep the surface areas in the final network
    with open("dfnGen_output/surface_area_Final.dat", "r") as fp:
        fp.readline()  # header
        for i in range(len(fractures)):
            if not fractures[i]["removed"]:
                line = fp.readline().split()
                fractures[i]["surface_area"] = float(line[0])

    local_print_log(f"--> There are {len(fractures)} fractures in the domain")
    local_print_log(f"--> There are {accepted_fractures} fractures in the final network")
    # Note could also return list of only accepted fractures
    return fractures


def combine_family_and_fracture_information(families, fractures, num_fractures,
                                            domain):
    """ Combines information from the fracture families and individual fractures, e.g., list of indicies . Creates the parameter dictionary. 

    Parameters
    -----------
        families : list
            List of dictionaries with information about fracture family
        
        fractures : list
            List of fracture dictionaries

        num_fractures : int
            Number of fractures

        domain : dict
            Dictionary of domain sizes 

    Returns
    --------
        families : list
            List of dictionaries with information about fracture family
        
        fractures : list
            List of fracture dictionaries
        
        params : dictionary
            Output report dictionary containing general parameters. See output_report for more details

    Notes
    ------
        None

    """

    colors = load_colors()
    # num_fractures, _, _, _, domain = parse_params_file(quiet=True)

    num_families = len(families)

    for ifam, family in enumerate(families):
        family["fracture list - all"] = []
        family["fracture list - final"] = []
        for i, fracture in enumerate(fractures):
            if fracture["family"] == family["Global Family"]:
                family["fracture list - all"].append(i)
                if not fracture["removed"]:
                    family["fracture list - final"].append(i)
        family["total_number_of_fractures"] = len(
            family["fracture list - all"])
        family["final_number_of_fractures"] = len(
            family["fracture list - final"])

        if num_families < 10:
            family["color"] = colors[2 * ifam]
        else:
            family["color"] = colors[ifam]

    params = {
        "num_families": num_families,
        "num_accepted_fractures": num_fractures,
        "num_total_fractures": len(fractures),
        "domain": domain,
        "final_color": "#4787ff",
        "all_color": "#ffe940",
        "analytic_color": "#ff4073"
    }

    return families, fractures, params
