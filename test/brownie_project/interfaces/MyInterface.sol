// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

// so what is this interface about? how to implement it?

interface MyInterface{
    function getValue(uint256 _index) external view returns (uint256);
    function setValue(uint256 _index, uint256 _value) external;
}