#!/usr/bin/env pytest-3
# -*- coding: utf-8 -*-

__author__     = "Maxime Raynal, Marc-Olivier Buob"
__maintainer__ = "Maxime Raynal, Marc-Olivier buob"
__email__      = "{maxime.raynal, marc-olivier.buob}@nokia.com"
__copyright__  = "Copyright (C) 2020, Nokia"
__license__    = "Nokia"


import configparser
import json
import os
import subprocess
import string

from collections import defaultdict
from glob import glob
from time import time
from pprint import pprint
from sklearn.metrics import adjusted_rand_score

from pybgl.html import html
from pybgl.regexp import compile_dfa
from pattern_clustering import PatternAutomaton, clustered_lines_to_html, make_dfa_any, language_density, pattern_clustering, MultiGrepFonctorLargest

TIME = "time"
PA = "parsing accuracy"
ARI = "adjusted rand index"
NUM_CLUSTERS = "number of clusters"

PC = "pattern clustering"
LM = "LogMine"
DR = "Drain"

PATH_TO_DRAIN_CONFIG = "./drain3config.ini"

# _____________________________________________________________________________
#                  PATTERN COLLECTION
# _____________________________________________________________________________

def load_pattern_collection(filename):
    with open(filename, 'r') as f:
        pattern_collection = json.load(f)
    return pattern_collection


def to_logmine_params(pattern_collection: dict):
    return [
        '"<%s>:/%s/"' % (
            name,
            re.replace("(", "\\(").replace(")", "\\)").replace("[", "\\[").replace("]", "\\]")
        )
        for name, re in pattern_collection.items()
    ]


def make_map_name_dfa_densities(
        map_name_re: dict,
        alphabet,
):
    map_name_dfa = {
        name: compile_dfa(re) if name != "any" else make_dfa_any()
        for name, re in map_name_re.items()
    }
    map_name_density = {
        name: language_density(dfa, alphabet)
        for (name, dfa) in map_name_dfa.items()
    }
    return map_name_dfa, map_name_density


# _____________________________________________________________________________
#                  DATASET
# _____________________________________________________________________________

def templates_from_csv(filename):
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    with open(filename, 'r') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        lines[i] = ','.join(lines[i].split(',')[1:])
        lines[i] = [
            _.rstrip().lstrip()
            for _ in lines[i].replace('"', "<*>").split('<*>')
            if any(letter in _ for letter in letters)
        ]
    return lines[1:]


def get_cluster_id(line, templates_uniques):
    uniques = []
    for cluster_id, unique in enumerate(templates_uniques):
        if all(u in line for u in unique):
            uniques.append(cluster_id)
    if len(uniques) == 1:
        return uniques[0]
    elif len(uniques) > 1:
        for unique in uniques:
            if all(
                    all(
                        _ in templates_uniques[unique]
                        for _ in templates_uniques[other_unique]
                    ) for other_unique in uniques if other_unique != unique
            ):
                return unique
            else:
                max_len = 0
                for unique in uniques:
                    new_len = sum(len(_) for _ in templates_uniques[unique])
                    if new_len > max_len:
                        max_len = new_len
                        best = unique
                return best
    else:
        pprint(templates_uniques)
        raise RuntimeError(
            "Could not identify cluster of this line:\n%s\n%s" %
            (line, [templates_uniques[unique] for unique in uniques])
        )


def load_data(root_log_path, load_modified=False, verbose=False):
    templates, logs = dict(), dict()
    for template_filename in glob(
        root_log_path + "*/*log_templates%s.csv" % (
            "_modified" if load_modified else ""
        )
    ):
        log_name = template_filename.split("/")[-1].split("_2k")[0]
        if verbose:
            print("Unpacking %s dataset ..." % log_name, end='')
        templates[log_name] = templates_from_csv(template_filename)
        if verbose:
            print("done")
            print("Checking %s integrity ...." % log_name, end='')
        with open(root_log_path + log_name + "/" + log_name + "_2k.log") as f:
            logs[log_name] = f.read().splitlines()
        for line in logs[log_name]:
            get_cluster_id(line, templates[log_name])
        if verbose:
            print("OK")
            print("")
    return templates, logs


# _____________________________________________________________________________
#                  CLUSTERING
# _____________________________________________________________________________

def get_ground_truth_as_list_of_sets(lines, templates):
    map_cluster_index = defaultdict(set)
    for i, line in enumerate(lines):
        clust_id = get_cluster_id(line, templates)
        map_cluster_index[clust_id].add(i)
    return [v for v in map_cluster_index.values()]


def get_ground_truth_as_list(lines, templates):
    return [get_cluster_id(line, templates) for line in lines]


def get_parsing_accuracy(obtained_clusters, lines, templates):
    ground_truth_clusters = get_ground_truth_as_list_of_sets(lines, templates)
    obtained_clusters = [set(cluster) for cluster in obtained_clusters]
    clusters_in_common = [
        c for c in obtained_clusters if c in ground_truth_clusters
    ]
    return sum(len(cluster) for cluster in clusters_in_common) / len(lines)


def get_rand_index(obtained_clusters, lines, templates):
    ground_truth_clusters = get_ground_truth_as_list(lines, templates)
    obt_clust_as_list = [None for _ in range(len(lines))]
    for i, cluster in enumerate(obtained_clusters):
        for j in cluster:
            obt_clust_as_list[j] = i
    if not all(_ is not None for _ in obt_clust_as_list):
        new_clust_id = max(
            set([_ for _ in obt_clust_as_list if _ is not None])
        ) + 1
        obt_clust_as_list = [
            _ if _ is not None else new_clust_id
            for _ in obt_clust_as_list
        ]
    return adjusted_rand_score(ground_truth_clusters, obt_clust_as_list)


METRICS = {
    "parsing accuracy": get_parsing_accuracy,
    "adjusted rand index": get_rand_index
}


def convert_to_list_of_indices(obtained_clusters, lines):
    result = []
    for cluster in obtained_clusters.values():
        current_item = []
        for line in cluster:
            current_item += [
                i for i, li in enumerate(lines) if li == line
            ]
        result.append(current_item)
    return result


# _____________________________________________________________________________
#                  LOGMINE
# _____________________________________________________________________________

def logmine_clustering(
        logmine_repo_path: str,
        file_path: str,
        k1: float = None,
        k2: float = None,
        max_dist: float = None,
        logmine_regexps: list = None,
        verbose=False
):
    call_args = [logmine_repo_path + "/logmine"]
    if k1 is not None:
        call_args += ["-k1", str(k1)]
    if k2 is not None:
        call_args += ["-k2", str(k2)]
    if max_dist is not None:
        call_args += ["-m", str(max_dist)]
    call_args += ["-i", "1"]
    call_args += [file_path]

    if len(logmine_regexps) > 0:
        call_args += ["-v"] + logmine_regexps
    if verbose:
        pprint(call_args)
    logmine_output = subprocess.check_output(call_args).decode('utf-8')
    if verbose:
        print(logmine_output)
    clusters = [
        [int(x) for x in line.split(' ')]
        for line in logmine_output.splitlines()
    ]
    return clusters


# _____________________________________________________________________________
#                  DRAIN
# _____________________________________________________________________________

def write_drain_config_file(
    map_name_re,
    extra_delimiters: list = ["_"],
    sim_th: float = 0.4,
    depth: int = 4,
    max_children: int = 100,
    max_clusters: int = 1024,
    path_to_config: str = PATH_TO_DRAIN_CONFIG,
):
    config = configparser.ConfigParser()
    config.read(path_to_config)

    config["MASKING"]["masking"] = json.dumps([
        {"regex_pattern": re, "mask_with": name}
        for name, re in map_name_re.items()
        if name != "any"
    ])
    config["DRAIN"]["sim_th"] = str(sim_th)
    config["DRAIN"]["depth"] = str(depth)
    config["DRAIN"]["max_children"] = str(max_children)
    config["DRAIN"]["max_clusters"] = str(max_clusters)

    with open(path_to_config, "w") as configfile:
        config.write(configfile)
try:
    from drain3 import TemplateMiner
    from drain3.template_miner_config import TemplateMinerConfig

    def drain_clustering(
            log_file_path: str,
            map_name_re,
            extra_delimiters: list = ["_"],
            sim_th: float = 0.4,
            depth: int = 4,
            max_children: int = 100,
            max_clusters: int = 1024,
            path_to_config: str = PATH_TO_DRAIN_CONFIG,
            show_clusters=False
    ):
        write_drain_config_file(
            map_name_re,
            extra_delimiters,
            sim_th,
            depth,
            max_children,
            max_clusters,
            path_to_config
        )

        config = TemplateMinerConfig()
        config.load(path_to_config)
        config.profiling_enabled = False
        template_miner = TemplateMiner(config=config)

        with open(log_file_path, 'r') as f:
            lines = f.readlines()
        clusters_as_dict = defaultdict(list)
        for i, line in enumerate(lines):
            cluster_id = template_miner.add_log_message(line)["cluster_id"]
            clusters_as_dict[cluster_id].append(i)
        if show_clusters:
            map_row_cluster = {
                row: cluster_id
                for cluster_id, rows in clusters_as_dict.items()
                for row in rows
            }
            html(clustered_lines_to_html(
                [line.strip() for line in lines],
                map_row_cluster=map_row_cluster,
                # line_to_html=lambda row, line: "%3d: %s" % (
                #     map_row_cluster[row], line
                # ),
                display_by_cluster=True
            ))
        return clusters_as_dict
except:
    print("Warning: could not load Drain")
    def drain_clustering(
            log_file_path: str,
            map_name_re,
            extra_delimiters: list = ["_"],
            sim_th: float = 0.4,
            depth: int = 4,
            max_children: int = 100,
            max_clusters: int = 1024,
            path_to_config: str = PATH_TO_DRAIN_CONFIG,
            show_clusters=False
    ):
        print("Error! Drain is not installed !!(https://github.com/IBM/Drain3)")

# _____________________________________________________________________________
#                  EVALUATION PIPELINE
# _____________________________________________________________________________

def evaluate_logmine_clustering(
        logmine_repo_path,
        file_path,
        ground_truth_templates,
        metrics,
        k1=None,
        k2=None,
        max_dist=None,
        logmine_regexps=None,
):
    if logmine_regexps is None:
        logmine_regexps = []
    start = time()
    clusters_as_list = logmine_clustering(
        logmine_repo_path,
        file_path,
        k1,
        k2,
        max_dist,
        logmine_regexps
    )
    computation_time = time() - start
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()
    results = {
        name: metric(clusters_as_list, lines, ground_truth_templates)
        for name, metric in metrics.items()
    }
    results[TIME] = computation_time
    results[NUM_CLUSTERS] = len(clusters_as_list)
    return results


def evaluate_drain_clustering(
    log_file_path: str,
    ground_truth_templates,
    metrics,
    map_name_re,
    extra_delimiters: list = ["_"],
    sim_th: float = 0.4,
    depth: int = 4,
    max_children: int = 100,
    max_clusters: int = 1024,
    path_to_config: str = PATH_TO_DRAIN_CONFIG,
    show_clusters=False
):
    start = time()
    clusters_as_dict = drain_clustering(
        log_file_path,
        map_name_re,
        extra_delimiters,
        sim_th,
        depth,
        max_children,
        max_clusters,
        path_to_config,
        show_clusters=show_clusters,
    )

    clusters_as_list = [v for v in clusters_as_dict.values()]
    computation_time = time() - start
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    results = {
        name: metric(clusters_as_list, lines, ground_truth_templates)
        for name, metric in metrics.items()
    }
    results[TIME] = computation_time
    results[NUM_CLUSTERS] = len(clusters_as_list)
    return results


def evaluate_fast_pattern_clustering(
        file_path,
        ground_truth_templates,
        metrics,
        map_name_dfa,
        map_name_density,
        max_dist,
        make_mg=MultiGrepFonctorLargest,
):
    start = time()
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()
    obtained_clusters = pattern_clustering(
        lines,
        map_name_dfa,
        [map_name_density[name] for name in sorted(map_name_dfa.keys())],
        max_dist,
        make_mg=make_mg
    )
    clusters_as_dict = defaultdict(set)
    for i, clust_id in enumerate(obtained_clusters):
        clusters_as_dict[clust_id].add(i)
    clusters_as_list = []
    for k, v in clusters_as_dict.items():
        clusters_as_list.append(list(v))
    computation_time = time() - start
    results = {
        name: metric(clusters_as_list, lines, ground_truth_templates)
        for name, metric in metrics.items()
    }
    results[TIME] = computation_time
    results[NUM_CLUSTERS] = len(clusters_as_dict)

    return results


def eval_on_all_logs_and_save(
        root_log_path,
        output_path,
        metrics,
        templates_dict,
        fundamental_collection,
        basic_collection,
        specific_collection,
        max_dist_pc_list,
        max_dist_logmine_list,
        drain_params_list,
        logmine_repo_path,
        multigrep_functor=MultiGrepFonctorLargest,
        logmine_regexps=None,
        alphabet=set(string.printable)

):
    result = defaultdict(lambda: defaultdict(dict))
    for sim_th in [a for a, b in drain_params_list]:
        for log_name in templates_dict:
            result[DR][log_name][sim_th] = dict()

    for log_name in templates_dict:
        file_path = root_log_path + log_name + "/" + log_name + "_2k.log"

        pc_collection = {**fundamental_collection, **basic_collection}
        dr_lm_collection = basic_collection
        if specific_collection is not None \
           and log_name in specific_collection.keys():
            pc_collection = {
                **pc_collection, **specific_collection[log_name]
            }
            dr_lm_collection = {
                **dr_lm_collection, **specific_collection[log_name]
            }

        map_name_dfa, map_name_density = make_map_name_dfa_densities(
            pc_collection, alphabet
        )
        lm_collection = to_logmine_params(dr_lm_collection)

        for max_dist in max_dist_pc_list:
            result[PC][log_name][max_dist] = evaluate_fast_pattern_clustering(
                file_path,
                templates_dict[log_name],
                metrics,
                map_name_dfa,
                map_name_density,
                max_dist,
                make_mg=multigrep_functor,
            )
            print(
                f"[PC][{log_name}][{max_dist}]: {result[PC][log_name][max_dist]}"
            )
        for max_dist in max_dist_logmine_list:
            result[LM][log_name][max_dist] = evaluate_logmine_clustering(
                logmine_repo_path,
                file_path,
                templates_dict[log_name],
                metrics,
                max_dist=max_dist,
                logmine_regexps=lm_collection
            )
            print(
                f"[LM][{log_name}][{max_dist}]: {result[LM][log_name][max_dist]}"
            )

        for sim_th, depth in drain_params_list:
            result[DR][log_name][sim_th][depth] = evaluate_drain_clustering(
                file_path,
                templates_dict[log_name],
                metrics,
                dr_lm_collection,
                sim_th=sim_th,
                depth=depth
            )
            print(
                f"[DR][{log_name}][{(sim_th, depth)}]: {result[DR][log_name][sim_th][depth]}"
            )
    with open(output_path, "w") as f:
        json.dump(result, f)


# _____________________________________________________________________________
#                  RESULT EXTRACTION
# _____________________________________________________________________________

def extract_metric_with_time(
    results,
    algorithm,
    metric,
):
    res_dict = dict()
    if algorithm == DR:
        for log_name in results[algorithm]:
            best_valus = -1
            best_time = None
            for sim_th, depths in results[algorithm][log_name].items():
                for depth in depths:
                    if best_valus < results[algorithm][log_name][sim_th][depth][metric]:
                        best_valus = results[algorithm][log_name][sim_th][depth][metric]
                        best_time = results[algorithm][log_name][sim_th][depth][TIME]
            res_dict[log_name] = (best_valus, best_time)
    else:
        for log_name in results[algorithm]:
            best_valus = -1
            best_time = None
            for max_dist in results[algorithm][log_name]:
                if best_valus < results[algorithm][log_name][max_dist][metric]:
                    best_valus = results[algorithm][log_name][max_dist][metric]
                    best_time = results[algorithm][log_name][max_dist][TIME]
            res_dict[log_name] = (best_valus, best_time)
    return res_dict


def extract_metric(
    results,
    algorithm,
    metric,
    logs_names_list=None
):
    if metric == "time":
        i = 1
        metric = "adjusted rand index"
    else:
        i = 0
    res = {
        k: v[i]
        for k, v in extract_metric_with_time(
                results, algorithm, metric
        ).items()
    }
    return [
        res[log_name]
        for log_name in (res if logs_names_list is None else logs_names_list)
    ]


def get_logs_name_order(
    results,
    algorithm,
    metric,
    sort_func=sorted
):
    if metric == "time":
        i = 1
        metric = "adjusted rand index"
    else:
        i = 0
    res = {
        k: v[i]
        for k, v in extract_metric_with_time(
                results, algorithm, metric
        ).items()
    }
    rev_res = {v: k for k, v in res.items()}
    return [rev_res[v] for v in sort_func(list(rev_res.keys()))]

# _____________________________________________________________________________
#                  RUNTIME EVALUATION
# _____________________________________________________________________________


def eval_runtime_pc(
        file_path,
        num_lines_to_cluster,
        map_name_dfa,
        multigrep_functor,
        map_name_density,
        max_dist,
):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    lines = lines[:min(len(lines), num_lines_to_cluster)]
    start = time()
    pattern_clustering(
        lines,
        map_name_dfa,
        [map_name_density[name] for name in sorted(map_name_dfa.keys())],
        max_dist,
        make_mg=multigrep_functor,
    )
    return time() - start


def eval_runtime_lm(
        file_path,
        num_lines_to_cluster,
        logmine_repo_path: str,
        k1: float = None,
        k2: float = None,
        max_dist: float = None,
        logmine_regexps: list = None,
):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    lines = lines[:min(len(lines), num_lines_to_cluster)]
    with open("./tmp.tmp", "w") as f_tmp:
        f_tmp.write("\n".join(lines))

    start = time()
    logmine_clustering(
        logmine_repo_path,
        "./tmp.tmp",
        k1,
        k2,
        max_dist,
        logmine_regexps
    )
    result = time() - start
    os.remove("./tmp.tmp")
    return result


def eval_runtime_drain(
        file_path,
        num_lines_to_cluster,
        map_name_re,
        extra_delimiters: list = ["_"],
        sim_th: float = 0.4,
        depth: int = 4,
        max_children: int = 100,
        max_clusters: int = 1024,
        path_to_config: str = PATH_TO_DRAIN_CONFIG,
):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    lines = lines[:min(len(lines), num_lines_to_cluster)]
    with open("./tmp.tmp", "w") as f_tmp:
        f_tmp.write("\n".join(lines))

    start = time()
    drain_clustering(
        "./tmp.tmp",
        map_name_re,
        extra_delimiters,
        sim_th,
        depth,
        max_children,
        max_clusters,
        path_to_config
    )
    result = time() - start
    os.remove("./tmp.tmp")
    return result
