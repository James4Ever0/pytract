// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

contract Faucet {
    receive() external payable {}

    function withdraw(uint withdraw_amount) public {
        require(withdraw_amount <= 1000);
		payable(msg.sender).transfer(withdraw_amount);
        // msg.sender.transfer(withdraw_amount);
    }
    function returnVars() public pure returns (uint, uint, uint) {
        uint var1 = 1;
        uint var2 = 2;
        uint var3 = 3;
        return (var1, var2, var3);
    }

    fallback() external payable {}
}
