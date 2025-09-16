#!/usr/bin/bash

SERVER=("~/backup/documents/" "~/backup/projects/")
CLIENT=("$HOME/documents/" "$HOME/projects/")

mkdir -p "${CLIENT[@]}"

ARG="--verbose --recursive --copy-links --hard-links -P --perms --times --delete --update --exclude-from=excludes.txt"

LOG=./bnr.log

if [ ! -e $LOG ]; then
    touch $LOG
fi


while [ : ]; do
    echo -n 'Type B for backup or R for restore: ' && read BOR

    case $BOR in
	[BbRr])
	    echo -n 'Enter Server IP address: '
	    read IP #&& SERVER="${IP}:$SERVER"

	    TEMP=temp.log
	    touch $TEMP

	    if [[ $BOR == [Bb] ]]; then
		rsync -e 'ssh -p 8022' --dry-run $ARG ${CLIENT[0]} $IP:${SERVER[0]} >> $TEMP
		rsync -e 'ssh -p 8022' --dry-run $ARG ${CLIENT[1]} $IP:${SERVER[1]} >> $TEMP
		BOR="Backup at $(date +%c)"
	    else
		rsync -e 'ssh -p 8022' --dry-run $ARG $IP:${SERVER[0]} ${CLIENT[0]} >> $TEMP
		rsync -e 'ssh -p 8022' --dry-run $ARG $IP:${SERVER[1]} ${CLIENT[1]} >> $TEMP
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
		rsync -e 'ssh -p 8022' $ARG ${CLIENT[0]} $IP:${SERVER[0]} | tee -a $LOG
		rsync -e 'ssh -p 8022' $ARG ${CLIENT[1]} $IP:${SERVER[1]} | tee -a $LOG
	    else
		echo $BOR >> $LOG
		rsync -e 'ssh -p 8022' $ARG $IP:${SERVER[0]} ${CLIENT[0]} | tee -a $LOG
		rsync -e 'ssh -p 8022' $ARG $IP:${SERVER[1]} ${CLIENT[1]} | tee -a $LOG
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
      
