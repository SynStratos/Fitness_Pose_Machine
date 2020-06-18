* "exercise_name": the name of the exercise for debugging needs (e.g. "Thruster")
* "angles_names": set of names of each used angle (e.g. ["elbow", "shoulder", "hip", "knee"])
* "angles_to_check": set of angles indexes managed for each different orientation ["s_e", "s_w"] (e.g. { "s_e": [0,2,6,8], "s_w": [1,3,7,9] }
* "push_pull": set of type of execution for each angle ["push", "pull"] (e.g. ["push", "push", "pull", "pull"])
* "mins": set of minimum value for each angle (e.g. [50, 65, 160, 160])
* "maxs": set of maximum value for each angle (e.g. [168, 169, 67, 51])
* "mids": set of medium values for each angle (e.g. [110, 120, 115, 105])
* "angles_order": set of expected order of angles. Angles in the same array are expected to occur in a close time range (e.g. [[2,3], [0,1]])
* "repetition_timeout": timeout for a single repetition expressed in seconds
* "total_timeout": total timeout before exiting the exercise, expressed in seconds
* "n_repetition": number of good repetition expected before ending the exercise
* "tolerance": range around the high threshold defined for each angle (e.g. [12, 12, 20, 16])
* "number_of_spikes": number of times each angle is expected to reach the threshold value (e.g. [1, 1, 1, 1])