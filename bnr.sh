#!/usr/bin/bash

# Parse command line arguments
PRESERVE_MODE=false
SYNC_MODE=false
while getopts "ps" opt; do
    case $opt in
        p)
            PRESERVE_MODE=true
            ;;
        s)
            SYNC_MODE=true
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            echo "Usage: $0 [-p] [-s]"
            echo "  -p: Preserve mode - disable --delete to keep files on destination"
            echo "  -s: Sync mode - bidirectional sync between client and server"
            exit 1
            ;;
    esac
done

# Validate that -p and -s are not used together
if [ "$PRESERVE_MODE" = true ] && [ "$SYNC_MODE" = true ]; then
    echo "Error: -p and -s options cannot be used together" >&2
    exit 1
fi

SERVER=("~/backup/documents/" "~/backup/projects/")
CLIENT=("$HOME/documents/" "$HOME/projects/")
mkdir -p "${CLIENT[@]}"

# Set rsync arguments based on mode
if [ "$SYNC_MODE" = true ]; then
    ARG="--verbose --recursive --copy-links --hard-links -P --perms --times --update"
    echo "Running in SYNC MODE: bidirectional sync (--delete disabled for safety)"
elif [ "$PRESERVE_MODE" = true ]; then
    ARG="--verbose --recursive --copy-links --hard-links -P --perms --times --update"
    echo "Running in PRESERVE MODE: --delete is disabled"
else
    ARG="--verbose --recursive --copy-links --hard-links -P --perms --times --delete --update"
fi

LOG=./bnr.log

# Function to run rsync with common excludes
run_rsync() {
    rsync -e 'ssh -p 8022' \
        --exclude='**/#*' \
        --exclude='**/.#*' \
        --exclude='**/.git/' \
        --exclude='**/__pycache__/' \
        --exclude='**/.venv/' \
        "$@"
}
if [ ! -e $LOG ]; then
    touch $LOG
fi
while [ : ]; do
    # In sync mode, skip the prompt and set BOR to 'S'
    if [ "$SYNC_MODE" = true ]; then
        BOR="S"
    else
        echo -n 'Type B for backup or R for restore: ' && read BOR
    fi
    case $BOR in
	[BbRr])
	    echo -n 'Enter Server IP address: '
	    read IP
	    TEMP=temp.log
	    touch $TEMP
	    if [[ $BOR == [Bb] ]]; then
		run_rsync --dry-run $ARG ${CLIENT[0]} $IP:${SERVER[0]} >> $TEMP
		run_rsync --dry-run $ARG ${CLIENT[1]} $IP:${SERVER[1]} >> $TEMP
		BOR="Backup at $(date +%c)"
	    else
		run_rsync --dry-run $ARG $IP:${SERVER[0]} ${CLIENT[0]} >> $TEMP
		run_rsync --dry-run $ARG $IP:${SERVER[1]} ${CLIENT[1]} >> $TEMP
		BOR="Restore at $(date +%c)"
	    fi
	    less $TEMP
	    
	    echo -n 'Proceed? [Y/N]: ' && read ANS
	    rm $TEMP
	    if [[ "$ANS" != [Yy] ]]; then
		continue
	    fi
	    rsync -e 'ssh -p 8022' --times --perms $IP:~/bnr.log $LOG 
	    if [[ $BOR == B* ]]; then
		echo $BOR >> $LOG
		run_rsync $ARG ${CLIENT[0]} $IP:${SERVER[0]} | tee -a $LOG
		run_rsync $ARG ${CLIENT[1]} $IP:${SERVER[1]} | tee -a $LOG
	    else
		echo $BOR >> $LOG
		run_rsync $ARG $IP:${SERVER[0]} ${CLIENT[0]} | tee -a $LOG
		run_rsync $ARG $IP:${SERVER[1]} ${CLIENT[1]} | tee -a $LOG
	    fi
	    echo '+++++++++++++++++++++++++++++++++++++++++++++++++++' >> $LOG
	    rsync -e 'ssh -p 8022' --times --perms $LOG $IP:~/bnr.log
	    
	    exit 0
	    ;;
	[Ss])
	    echo -n 'Enter Server IP address: '
	    read IP
	    TEMP=temp.log
	    touch $TEMP

	    # Dry-run both directions for preview
	    echo "=== Syncing Client -> Server ===" >> $TEMP
	    run_rsync --dry-run $ARG ${CLIENT[0]} $IP:${SERVER[0]} >> $TEMP
	    run_rsync --dry-run $ARG ${CLIENT[1]} $IP:${SERVER[1]} >> $TEMP
	    echo "" >> $TEMP
	    echo "=== Syncing Server -> Client ===" >> $TEMP
	    run_rsync --dry-run $ARG $IP:${SERVER[0]} ${CLIENT[0]} >> $TEMP
	    run_rsync --dry-run $ARG $IP:${SERVER[1]} ${CLIENT[1]} >> $TEMP

	    less $TEMP

	    echo -n 'Proceed? [Y/N]: ' && read ANS
	    rm $TEMP
	    if [[ "$ANS" != [Yy] ]]; then
		continue
	    fi

	    # Sync log file from server
	    rsync -e 'ssh -p 8022' --times --perms $IP:~/bnr.log $LOG

	    # Perform bidirectional sync
	    BOR="Sync at $(date +%c)"
	    echo $BOR >> $LOG

	    echo "Syncing Client -> Server..."
	    run_rsync $ARG ${CLIENT[0]} $IP:${SERVER[0]} | tee -a $LOG
	    run_rsync $ARG ${CLIENT[1]} $IP:${SERVER[1]} | tee -a $LOG

	    echo "Syncing Server -> Client..."
	    run_rsync $ARG $IP:${SERVER[0]} ${CLIENT[0]} | tee -a $LOG
	    run_rsync $ARG $IP:${SERVER[1]} ${CLIENT[1]} | tee -a $LOG

	    echo '+++++++++++++++++++++++++++++++++++++++++++++++++++' >> $LOG
	    rsync -e 'ssh -p 8022' --times --perms $LOG $IP:~/bnr.log

	    exit 0
	    ;;
	*)
	    echo 'Invalid input'
	    ;;
    esac
done
