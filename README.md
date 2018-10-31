# deco.ai

A Decentralized Ecosystem for Artificial Intelligence


# OVERVIEW

This platform will allow a developer to deploy, run, and sell their AI services. There are no centralized servers for this platform. Therefore, everything runs completely decentralized on the blockchain. As long as there is at least one person running a node at all times, then the network could, thereotically, never be taken down.


# HOW TO RUN

This has only been tested on linux systems. It may work for other machines with little modification to the network parameters.
Make sure you have python 3.6 installed.

- Open command prompt to file directory /deco.ai
- run python3.6 blockchain.py -p -5000

This will intialized the blockchain and start the server.

- Go into a browser on the local machine and enter the IP address stated in the terminal (eg. http://0.0.0.0:5000)

You can see the deco.ai interface.

- click network and click sync to get the latest blockchain

# CURRENT LIMITATION

- only thing working on the frontend is the connection to the latest blockchain
- the backend GET and POST request work for all transactions needed to run deco.ai
