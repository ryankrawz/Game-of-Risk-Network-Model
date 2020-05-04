# Welcome to the Game of Risk!

The Game of Risk Network Model is a digital version of the Game of Risk that operates on an underlying graph data structure. The backend of the application consists of a Python object-oriented system, with a core class initialized by providing the path to a text data file containing the information for a game. Objects are also initialized to represent players, cards, and territories on the board. For the front end, the application implements the NetworkX library to visualize the graph by taking advantage of NetworkX’s Matplotlib drawing tools that are specifically designed for networks. The distinctive feature of the program is its ability to accept a data file from the user to determine the game board and the number of players, which makes the games entirely configurable to the user’s liking. An interesting additional functionality is the support for computer players, which allows a human user to test their strategic skills against formidable opponents even when playing alone. 

## Check out this demo for how to play
[![Alt text](https://img.youtube.com/vi/dcE5snxpASA/0.jpg)](https://www.youtube.com/watch?v=dcE5snxpASA)

## More on data file format
```
Star Wars Episode V: The Empire Strikes Back
1|Rebel Alliance
2|Jedi|Empire
Mount Ison|Hoth|North Ridge
North Ridge|Hoth|Mount Ison|Hanging Valley|Cirque Glacier|Lanteel Glacier
Hanging Valley|Hoth|North Ridge|Cirque Glacier|Clabburn Range
...
```
Here's an example of a text data file to configure the game, whose file path is provided as a string for the only argument of the `GameOfRisk` class. The first line is the title. The second line declares `n` human players, formatted like so:
```
n|HumanPlayer_1|HumanPlayer_2|...|HumanPlayer_n
```
The third line declares computer players in the same style as human players. If there's zero human or computer players in a game, simply include a `0` for the corresponding line. All following lines declare territories and their neighbors with the following format:
```
TerritoryName|TerritoryContinent|TerritoryNeighbor_1|TerritoryNeighbor_2|...|TerritoryNeighbor_n
```
The `|` symbol is used as a delimeter. Any territories missing a continent or only listed as neighbors and not specified themselves will raise an exception during initialization. Feel free to try any war in history or fantasy. Some interesting ideas are: Game of Thrones, Lord of the Rings, Harry Potter, and Star Trek!
