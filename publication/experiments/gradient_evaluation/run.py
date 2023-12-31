#!/usr/bin/python3

# TODO: License goes here

# Script to perform a parameter sweep over a certain range in a certain dimension of
# a program generated by discograd. It supports the automated testing of multiple backends
# and their hyperparameters. Outputs csv-formatted files in the "results" folder. The 
# files are named according to a fixed scheme, which includes the (hyper-)parameters for
# easy evaluation.
# 
# Usage:
# ======
# Define a file named "experiment.py" (preferrably in a separate folder), which defines the
# dictionaries "programs = {...}" and "estimators = {...}". Call this file with the path
# to the folder where the exdperiment file is stored. You may use the contents of the
# existing "experiments" folder as a reference.
# For the CLI definition, cf. to the bottom of this file or call -h for help.

import numpy as np
import sys
import argparse
from itertools import product
from time import time as pythons_time
from multiprocessing import Process
import functools

sys.path.append('.')
sys.path.append('..')
from estimator_wrappers import *

out_path = "results"

def get_fname(out_path, prog_name_clean, stddev, seed, nreps, estim, estim_param_str, dim, estimator_replication):
  """return the filename of the givene program parametrization."""
  return f"{out_path}/{prog_name_clean}_stddev={stddev}_seed={seed}_nreps={nreps}-{estim['name']}_{estim_param_str}-dim_{dim:03d}-replication_{estimator_replication:04d}.txt"

def run(prog, estim):
  # TODO: this should be removed
  # set random seed (for the case that an experiment specification uses numpys rng)
  np.random.seed((id(prog) ^ id(estim)) % 2**32)

  # normalize estimator dictionary values to be tuples
  for k, v in estim['params'].items():
    if isinstance(v, (float, int)):
      estim['params'][k] = (v,)

  # determine the dimension in which the sweep is performed as the entry
  # in the params tuple that is not a number (i.e. a list of sampling points
  # or a function for generating sampling points) for that particular
  # component of the input vector
  dim = 0
  prog['params'] = list(prog['params'])
  for i, v in enumerate(prog['params']):
    if isinstance(v, (float, int)):
      prog['params'][i] = (v,)
    else:
      dim = i

  estim_param_names = list(estim['params'].keys())
  estim_param_vals = list(estim['params'].values())
  estim_param_combs = tuple(dict(zip(estim_param_names, list(param_val))) for param_val in product(*estim_param_vals))
  rs = np.random.RandomState() # set random numpy seed
  for estim_param_comb in estim_param_combs:
    for estimator_replication in range(num_estimator_replications):
      estim_param_str = '-'.join([f"{k}={v}" for k, v in estim_param_comb.items()])
      # normalize program dictionary values to be tuples
      if isinstance(prog['stddevs'], (float, int)):
        prog['stddevs'] = (prog['stddevs'],)
      if isinstance(prog['seed'], (float, int)):
        prog['seed'] = (prog['seed'],)
      # drop support for multiple seeds or nreps per thread for now
      if len(list(prog['seed'])) > 1 or len(list(prog['nreps'])) > 1:
        print("multiple seeds or nreps per line not supported")
        exit()
      for stddev in prog['stddevs']:
        for seed in prog['seed']: 
          num_paths = None
          for nreps in prog['nreps']:
            start_time = pythons_time()
            prog_name_clean = prog['name'].replace('/', '_')

            fname = get_fname(out_path, prog_name_clean, stddev, seed, nreps, estim, estim_param_str, dim, estimator_replication)

            print(f"{fname} started")
       
            with open(fname, 'w') as f:

              # if 
              if isinstance(prog['params'][0], functools.partial):
                prog_param_combs = [prog['params'][0](rs)]
                num_prog_params = len(prog_param_combs[0])
              else:
                prog_param_combs = product(*prog['params'])
                num_prog_params = len(prog['params'])
               
              f.write(','.join([f"x{i}" for i in range(num_prog_params)]) + ',y,' + ','.join([f"dydx{i}" for i in range(num_prog_params)]) + ",cumulative_time\n")
              cumulative_time = 0.0

              # perform parameter swipe
              for prog_param_comb in prog_param_combs:
                if 'return_num_paths' in estim_param_comb:
                  assert(nreps == 1)
                  output, derivs, time, num_paths = globals()[estim['name']](prog['name'], stddev, seed, nreps, np.asarray(prog_param_comb), estim_param_comb)
                else:
                  output, derivs, time = globals()[estim['name']](prog['name'], stddev, seed, nreps, np.asarray(prog_param_comb), estim_param_comb)
                cumulative_time += time
                f.write(','.join(map(str, prog_param_comb)) + ',' + str(output) + ',' + ','.join(map(str, derivs)) + "," + str(time) + "\n")
                f.flush()

          finish_time = pythons_time()
          print(f"{fname} took {finish_time - start_time:.2f}s (cumulative estimation time was {cumulative_time*1e-6:.6f}s)" + (f", num_paths: {num_paths}" if num_paths else ""))

if __name__ == "__main__":
  parser = argparse.ArgumentParser(prog="run.py")
  parser.add_argument("experiment_path", type=str)
  parser.add_argument("--num_reps", "-r", type=int, default=1)
  parser.add_argument("--sequential", "-s", default=False, action="store_true")
  args = parser.parse_args()

  num_estimator_replications = args.num_reps
  # import experiment specification from the file named experiment.py
  sys.path.append(args.experiment_path)
  from experiment import programs, estimators

  processes = [Process(target=run, args=arg) for arg in product(programs, estimators)]
  for process in processes:
    process.start()
    if args.sequential:
      process.join()

  if not args.sequential:
    for process in processes:
      process.join()

