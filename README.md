# processing-airport-data

This is a set of small program to process the data out of the measurement station at the Ursulinen.

Change the basic settings like parent director, partecto number or time to load in params.py 

The data is read in with the set of readin___.py

The first steps of processing (1-4) scramble additional information on the single flights and save them to the datafram of the flights.
This additional info is:

- gps info (minimum distance, minimum distance time, overflight from)
- aircraft information
- weather during the flight

Step 4 and 5 you can ignor, right?

Then you have the plotting scrips:


