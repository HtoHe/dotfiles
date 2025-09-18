#!/usr/bin/bash
SERVER=("~/backup/documents/" "~/backup/projects/")
CLIENT=("$HOME/documents/" "$HOME/projects/")
mkdir -p "${CLIENT[@]}"
ARG="--verbose --recursive --copy-links --hard-links -P --perms --times --delete --update"
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
    echo -n 'Type B for backup or R for restore: ' && read BOR
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
	*)
	    echo 'Invalid input'
	    ;;
    esac
done
