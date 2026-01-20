import React from "react";
import styled from "styled-components";

const Buttonwow = ({ handleUpload }) => {
  return (
    <StyledWrapper>
      <button className="c-button" onClick={handleUpload}>
        <span className="c-main">
          <span className="c-ico"></span>
          submit
        </span>
      </button>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  button {
    border: none;
  }

  .c-button {
    background: linear-gradient(
      140deg,
      rgba(75, 118, 200, 1) 0%,
      rgba(31, 70, 145, 1) 100%
    );
    border-radius: 15px;
    font-size: 20px;
    text-align: left;
    padding: 11px 0px 11px 0px;
    // border: 4px solid rgb(37, 37, 37) !important;
    // border-style: outset;
    box-shadow: 6px 10px 18px rgba(253, 252, 252, 0.1);
    cursor: pointer;
    height: 6vh;
  }

  .c-button .c-main {
    border-radius: 15px;
    // height:2vh;
    color: rgba(255, 255, 255, 1);
    padding: 11px 25px 11px 11px;
    box-shadow: inset 0px 0px 5px rgba(17, 17, 17, 0);
    transition: all 0.5s ease-in-out;
    border: 1px solid transparent;
  }

  .c-ico .c-blur {
    background: linear-gradient(
      318deg,
      rgba(75, 118, 200, 1) 0%,
      rgba(31, 70, 145, 1) 100%
    );
    border-radius: 100%;
    margin-left: 0;
    padding: 8px 23px;
    filter: blur(1px);
    text-align: center;
  }

  .c-ico {
    position: relative;
    margin-right: 20px;
  }

  .c-ico .ico-text {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }

  /* Hovering */

  .c-button .c-main:hover {
    box-shadow: inset 0px 0px 5px rgba(17, 17, 17, 0.6);
    border: 1px solid rgba(26, 26, 26, 0.5);
    color: rgba(255, 255, 255, 0.5);
    height: 5vh;
  }
`;

export default Buttonwow;
