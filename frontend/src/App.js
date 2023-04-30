import React, { useState } from "react";
import "./App.css";

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [output, setOutput] = useState(null);
  const [awaitingOutput, setAwaitingOutput] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    // Frontend rejection if the image is still being processed.
    if (awaitingOutput) {
      return;
    }

    // fetch("http://localhost:3000/generate")
    console.log("Image submitted:", image);

    // Only for testing
    setOutput(preview);

  };

  const handleFileChange = (event) => {
    setImage(event.target.files[0]);

    // Create a preview of the uploaded image.
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(event.target.files[0]);

  };

  return (
    <div className="App">
      <header className="App-header">
        <h1 className="text-shadow">Ha<span className="emphasis">loop</span>inate</h1>
        <h2>A deep-dream looping GIF generator</h2>
      </header>
      <form onSubmit={handleSubmit}>
        <div className="image-io">
          <div className="image-input">
            <h3>Input</h3>
            <img className="input" src={preview ? preview : "https://via.placeholder.com/256"} alt="Input"/>
          </div>
          <div style={{"width" : "2rem"}}></div>
          <div className="image-output">
            <h3>Output</h3>
            <img className="output" src={output ? output : "https://via.placeholder.com/256"} alt="Output"/>
          </div>
        </div>
        <input type="file" accept="image/*" onChange={handleFileChange} required/>
        <button type="submit">Generate!</button>
      </form>
      <footer className="App-footer">
        <div className="credits">
          © 2023 Joshua Ong, Alston Lo, Jamie Zhao
        </div>
        <div className="github-link">
          <a href="https://github.com/ArKane-6418/TreasureHacks3.5"><img className="github" src="logo-github.svg" alt="github"></img></a>
        </div>
      </footer>
    </div>
  );
}

export default App;