# team_2020

PolyHACK 2020: ELCA Challenge - Traffic optimization with real-time simulation  
Team Members: Amaris Chen, Chi-Ching Hsu, Ya-Chi Yu, Ting-Yu Chen  
chenam@student.ethz.ch, hsuch@student.ethz.ch, yuyachi@student.ethz.ch, tinchen@student.ethz.ch  
Date: 2020 November 7-8  

* Detailed description of our project and approach can be found [here](https://github.com/ElcaPolyHack2020/team_2020/blob/main/ELCA_Challenge_Team_2020.pdf).
* Our run statistics can be found [here](https://github.com/ElcaPolyHack2020/team_2020/blob/main/run_statistics.csv).
* Demo of our simulation running for 10800 timesteps below. [![here](http://i3.ytimg.com/vi/Uk3Eflc-Wg0/hqdefault.jpg)](https://youtu.be/Uk3Eflc-Wg0)  


## Our Algorithm

First, we bucket all the pedestrians by their depart time into buckets of time intervals. We dispatch our buses by time intervals to pick our passengers.

### Greedy I: Optimal Drop-off
This version of our algorithm picks up all the neighboring passengers within the same time bucket. Once all the passengers are onboard, we find an optimal route to drop them off based on the next nearest drop-off destination.

### Greedy II: Optimal Pick-up and Drop-off
This version of our algorithm picks up the first passenger in the group, and adds the first passenger's drop-off point to the "possible_routes" list. Then we add the second passenger's pick-up point to "possible_routes" list as well. We plan the bus' next stop based on the nearest destination (shortest route) in the list. This idea is similar to how Uber pool works.


## Run Results

| Methods | Buses Dispatched | Pedestrians picked up | Route Length | Total Wait Time (waiting time x Pedestrians picked up) |
|---------|------------------|-----------------------|--------------|-----------------|
| Greedy I | 58022 | 5583 | 17554.98 | 3795044.25 |
| Greedy II | 58022 | 5590 | 14881.37 | 4728301.5 |

### To run:

The simulation can be started by running ```python3 main.py``` with the default settings.

An example of running command is:
```python
python3 main.py --capacity 4 --interval 15 --seed 30 --steps 86400 --stopDuration 5

```