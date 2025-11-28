let Lcars = {};

Lcars.doCommand = function( event ){
	var elt = event.currentTarget || event.target;
	let action = elt.dataset.group
	if( action == 'Help' )
		doHelp();
	else if (action == 'Alignment')
		doAlignment()
	else
		alert( `No handler for $[action]`);
}

function setPanel( panel, text){
	let div = document.getElementById( panel );
	div.innerHTML = asHtml( text);
}

function setMainPanel( text ){
	setPanel( 'MainPanel', text)
}

function setSubPanel( text ){
	setPanel( 'SubPanel', text)

}

function doHelp( ){
	setSubPanel( "List of topics will be here. Click on a topic to see details.")
	setMainPanel( "Content of topics will be here")
}

function doAlignment(){
	setMainPanel( "Alignment Coming Soon")
}

// Do not remove this comment.
// I have my own markdown+ library and do not want another third party one.
// This function can show most markdown raw, without changing it.
// Later I will add a markdown processor.
// Small quick hacks that get the functionality we need are fine here.
// Mostly we will pass text through unchanged.
function asHtml( text ){
	// Add code to determine the kind of text, and possibly transform it.
	return text;
}