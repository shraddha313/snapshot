To run the Snapshot algorithm,

1. Open 4 terminals
2. Run the following commands on each terminal
	 python snapshot.py <process name> configuration_file.txt post_file.txt (The process names are present in the configuration file along with the port number)

Implementation handles 4 processes and assumes connection is stable between them before any event occurs.

To take Snapshot : The user needs to input on console : Snap

Working:
1. Processes randomly exchange money between them.
2. When "Snap" is input by user. The user wants to know the global snapshot of the system.
3. In the current implementation, Each process will store its own Snapshot after receiving markers from all the incoming channels. Thus the global snapshot is obtained.

