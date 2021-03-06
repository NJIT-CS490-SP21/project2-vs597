import React from 'react';
import { Board } from './Board.js';

export function LoginDisplay(props) {
    const spectators = props.Spectators;
    console.log(props.PlayerX);
    console.log(props.PlayerO);
    console.log(spectators);
    return (
        <div className="greeting">
            <div className="tictac">
              <h1>My Tic Tac Toe Board</h1>
              {<Board PlayerX={props.PlayerX} PlayerO={props.PlayerO} Spectators={props.Spectators} username={props.username}/>}
            </div>
            <div className="userslist">
              <ul>
                Player X: {props.PlayerX}
              </ul>
              <ul>
                Player O: {props.PlayerO}
              </ul>
              <ol>
                Spectators: {spectators.map(spectator => (
                  <li>{spectator}</li>
                ))}
              </ol>
            </div>
      </div>
    );
}



        