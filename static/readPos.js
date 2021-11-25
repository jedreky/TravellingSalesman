// declare constants
const R = 3.5;
const red = '#FF0000';

// intialise an array to store points
let points = new Array();

document.getElementById('click-area').onclick = function clickEvent(e)
{
	// compute coordinates
	let canvas = e.target;
	let rect = e.target.getBoundingClientRect();
	let x = e.clientX - rect.left;
	let y = e.clientY - rect.top;

	// draw a circle on the canvas
	if (canvas.getContext)
	{
		let ctx = canvas.getContext('2d');
		ctx.beginPath();
		ctx.arc(x, y, R, 0, 2 * Math.PI, false);
		ctx.lineWidth = 3;
		ctx.fillStyle = red;
		ctx.strokeStyle = red;
		ctx.fill();			
		ctx.stroke();
	}

	// add the coordinates to the list
	x = x.toFixed(3);
	y = y.toFixed(3);
	points.push( '[' + x + ', ' + y + ']' );
	document.getElementById('points').value = points;
	document.getElementById('info').innerHTML = 'You have selected ' + points.length + ' points.';
}
