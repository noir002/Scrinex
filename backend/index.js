// yargs simplifies parsing and handling command-line arguments.

const yargs = require("yargs");
const { hideBin } = require("yargs/helpers"); // Passes only the user-provided arguments to yargs.

const {initRepo} = require('./controllers/init');
const {addRepo} = require('./controllers/add');

yargs(hideBin(process.argv))
  .command("init", "Purpose: Initialize a new repository", {}, initRepo)
  .command("add <file>", "Purpose: Add a file", (yargs) => {
    yargs.positional("file", {
        describe: "File to add to the staging area",
        type: "String",
    });
  }, addRepo)
  .demandCommand(1, "Enter a command")
  .help()
  .parse();

