pragma solidity 0.6.4;

contract Faucet {
	receive() external payable{}

	function withdraw (uint withdraw_amount) public {
		require(withdraw_amount <= 1000);
		msg.sender.transfer(withdraw_amount);
	}

	fallback() external payable{}
}