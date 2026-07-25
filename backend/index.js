// yargs simplifies parsing and handling command-line arguments.

const yargs = require("yargs");
const { hideBin } = require("yargs/helpers"); // Passes only the user-provided arguments to yargs.

const {initRepo} = require('./controllers/init');
const {addRepo} = require('./controllers/add');
const {commitRepo} = require('./controllers/commit');
const {pushRepo} = require('./controllers/push');
const {pullRepo} = require('./controllers/pull');
const {revertRepo} = require('./controllers/revert');

yargs(hideBin(process.argv))
  .command("init", "Purpose: Initialize a new repository", {}, initRepo)
  .command("add <file>", "Purpose: Add a file", (yargs) => {
    yargs.positional("file", {
        describe: "File to add to the staging area",
        type: "String",
    });
  }, addRepo)
  .command("commit <message>", "Purpose: Commit changes", (yargs) => {
    yargs.positional("message", {
        describe: "Commit message",
        type: "String",
    });
  }, commitRepo)
  .command("push", "Purpose: Push changes to remote repository", {}, pushRepo)
  .command("pull", "Purpose: Pull changes from remote repository", {}, pullRepo)
  .command("revert", "Purpose: Revert changes", {}, revertRepo)
  .demandCommand(1, "Enter a command")
  .help()
  .parse();

