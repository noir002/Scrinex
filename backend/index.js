// yargs simplifies parsing and handling command-line arguments.

const yargs = require("yargs/yargs");
const { hideBin } = require("yargs/helpers"); // Passes only the user-provided arguments to yargs.

const {initRepo} = require('./controllers/init');

yargs(hideBin(process.argv))
  .command("init", "Purpose: Initialize a new repository", {}, initRepo)
  .demandCommand(1, "Enter a command")
  .help()
  .parse();

