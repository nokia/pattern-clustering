#!/usr/bin/env pytest-3
# -*- coding: utf-8 -*-

__author__     = "Maxime Raynal, Marc-Olivier Buob"
__maintainer__ = "Maxime Raynal, Marc-Olivier buob"
__email__      = "{maxime.raynal, marc-olivier.buob}@nokia.com"
__copyright__  = "Copyright (C) 2020, Nokia"
__license__    = "Nokia"

from pathlib import Path
import configparser
import json
import tempfile
import subprocess
import string

from collections import defaultdict
from time import time
from pprint import pprint
from sklearn.metrics import adjusted_rand_score

from pybgl.html import html
from pybgl.regexp import compile_dfa
from pattern_clustering import clustered_lines_to_html, make_dfa_any, language_density, pattern_clustering, MultiGrepFunctorLargest

TIME = "time"
PA = "parsing accuracy"
ARI = "adjusted rand index"
NUM_CLUSTERS = "number of clusters"

PC = "pattern clustering"
LM = "Logmine"
DR = "Drain"

PATH_TO_DRAIN_CONFIG = "./drain3config.ini"

#---------------------------------------------------------------
#                 PATTERN COLLECTION
#---------------------------------------------------------------

def load_pattern_collection(filename: Path):
    with open(filename, 'r') as f:
        return json.load(f)


def to_logmine_params(pattern_collection: dict):
    return [
        '"<%s>:/%s/"' % (
            name,
            re.replace("(", "\\(").replace(")", "\\)").replace("[", "\\[").replace("]", "\\]")
        )
        for (name, re) in pattern_collection.items()
    ]


def make_map_name_dfa_densities(map_name_re: dict, alphabet: set) -> tuple:
    map_name_dfa = {
        name: compile_dfa(re) if name != "any" else make_dfa_any()
        for name, re in map_name_re.items()
    }
    map_name_density = {
        name: language_density(dfa, alphabet)
        for (name, dfa) in map_name_dfa.items()
    }
    return (map_name_dfa, map_name_density)


#---------------------------------------------------------------
#                 DATASET
#---------------------------------------------------------------

def load_template_from_csv(filename: Path):
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


def get_cluster_id(line: str, templates_uniques: list):
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

def canonic_log_name(log_path: Path):
    return log_path.with_suffix('').name.split("_2k")[0]

def load_data(
    log_dir: Path,
    load_modified: bool = False,
    verbose: bool = False
) -> tuple:
    def message(*cls, **kwargs):
        if verbose:
            print(*cls, **kwargs)
    def make_template_path(log_name: str) -> Path:
        suffix = "_templates_modified.csv" if load_modified else "_templates.csv"
        return log_name.parent / (log_name.name + suffix)

    templates, logs = dict(), dict()
    for log_path in log_dir.glob("*/*.log"):
        log_name = canonic_log_name(log_path)
        message(f"Loading [{log_name}] dataset (load_modified={load_modified})")

        # Load the log file
        message(f"  Loading [{log_path}] log", end="... ")
        with open(log_path) as f:
            logs[log_name] = f.read().splitlines()
        message("OK")

        # Load the appropriate template
        template_path = make_template_path(log_path)
        message(f"  Loading [{template_path}] template", end="... ")
        templates[log_name] = load_template_from_csv(template_path)
        message("OK")

        # Check if the template is compliant with the log file
        message(f"  Checking integrity", end="... ")
        for line in logs[log_name]:
            get_cluster_id(line, templates[log_name])
        message("OK")
    return (templates, logs)


#---------------------------------------------------------------
#                 CLUSTERING
#---------------------------------------------------------------

def get_ground_truth_as_list_of_sets(lines: list, templates: list) -> list:
    map_cluster_index = defaultdict(set)
    for (i, line) in enumerate(lines):
        clust_id = get_cluster_id(line, templates)
        map_cluster_index[clust_id].add(i)
    return [v for v in map_cluster_index.values()]


def get_ground_truth_as_list(lines: list, templates: list) -> list:
    return [get_cluster_id(line, templates) for line in lines]


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


#---------------------------------------------------------------
#                 METRICS
#---------------------------------------------------------------

def parsing_accuracy(obtained_clusters: list, lines: list, templates: list) -> float:
    ground_truth_clusters = get_ground_truth_as_list_of_sets(lines, templates)
    obtained_clusters = [set(cluster) for cluster in obtained_clusters]
    clusters_in_common = [
        c for c in obtained_clusters if c in ground_truth_clusters
    ]
    return sum(len(cluster) for cluster in clusters_in_common) / len(lines)


def adjusted_rand_index(obtained_clusters: list, lines: list, templates: list) -> float:
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
    "parsing accuracy": parsing_accuracy,
    "adjusted rand index": adjusted_rand_index
}


#---------------------------------------------------------------
#                 LOGMINE
#---------------------------------------------------------------

def logmine_clustering(
        logmine_repo_path: Path,
        file_path: str,
        k1: float = None,
        k2: float = None,
        max_dist: float = None,
        logmine_regexps: list = None,
        verbose: bool = False
):
    call_args = [str(logmine_repo_path / "logmine")]
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


#---------------------------------------------------------------
#                 DRAIN
#---------------------------------------------------------------

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
            map_name_re: dict,
            extra_delimiters: list = ["_"],
            sim_th: float = 0.4,
            depth: int = 4,
            max_children: int = 100,
            max_clusters: int = 1024,
            path_to_config: str = PATH_TO_DRAIN_CONFIG,
            show_clusters: bool = False
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
        for (i, line) in enumerate(lines):
            cluster_id = template_miner.add_log_message(line)["cluster_id"]
            clusters_as_dict[cluster_id].append(i)

        if show_clusters:
            display_clustering(lines, list(clusters_as_dict.values()))
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


#---------------------------------------------------------------
#                 NOTEBOOK UTILITIES
#---------------------------------------------------------------

def clustering_to_html(lines: list, clusters_as_list: list) -> str:
    map_row_cluster = {
        row: cluster_id
        for (cluster_id, rows) in enumerate(clusters_as_list)
        for row in rows
    }
    return clustered_lines_to_html(
        [line.strip() for line in lines],
        map_row_cluster=map_row_cluster,
    )


def display_clustering(lines: list, clusters_as_list: list):
    html(clustering_to_html(lines, clusters_as_list))


#---------------------------------------------------------------
#                 EVALUATION PIPELINE
#---------------------------------------------------------------

def evaluate_logmine_clustering(
        logmine_repo_path: Path,
        file_path: Path,
        ground_truth_templates,
        metrics,
        k1=None,
        k2=None,
        max_dist: float =None,
        logmine_regexps=None,
        show_clusters: bool = False
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

    if show_clusters:
        display_clustering(lines, clusters_as_list)
    return results


def evaluate_drain_clustering(
    log_file_path: Path,
    ground_truth_templates: dict,
    metrics: dict,
    map_name_re: dict,
    extra_delimiters: list = ["_"],
    sim_th: float = 0.4,
    depth: int = 4,
    max_children: int = 100,
    max_clusters: int = 1024,
    path_to_config: str = PATH_TO_DRAIN_CONFIG,
    show_clusters: bool =False
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

    if show_clusters:
        display_clustering(lines, clusters_as_list)
    return results


def evaluate_pattern_clustering(
        file_path: Path,
        ground_truth_templates: dict,
        metrics: dict,
        map_name_dfa: dict,
        map_name_density: dict,
        max_dist: float,
        make_mg: callable = MultiGrepFunctorLargest,
        show_clusters: bool = False
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

    if show_clusters:
        display_clustering(lines, clusters_as_list)
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
        multigrep_functor=MultiGrepFunctorLargest,
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


#---------------------------------------------------------------
#                 RESULT EXTRACTION
#---------------------------------------------------------------

def extract_metric_with_time(
    results: dict,
    algorithm: str,
    metric: str,
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

#---------------------------------------------------------------
#                 RUNTIME EVALUATION
#---------------------------------------------------------------

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

    with tempfile.NamedTemporaryFile() as f_tmp:
        print("\n".join(lines), file=f_tmp)
        start = time()
        logmine_clustering(
            logmine_repo_path,
            tmp.name,
            k1,
            k2,
            max_dist,
            logmine_regexps
        )
        result = time() - start

    return result


def eval_runtime_drain(
        file_path,
        num_lines_to_cluster: int,
        map_name_re: dict,
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

    with tempfile.NamedTemporaryFile() as f_tmp:
        print("\n".join(lines), file=f_tmp)
        start = time()
        drain_clustering(
            tmp.name,
            map_name_re,
            extra_delimiters,
            sim_th,
            depth,
            max_children,
            max_clusters,
            path_to_config
        )
        result = time() - start

    return result
