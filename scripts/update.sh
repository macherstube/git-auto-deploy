#!/bin/bash

. ../config/default

baseURL(){
  echo "https://api.github.com/repos/$1/$2"
}

getJSON(){
	echo $(curl -sL "$1" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Authorization: token $AUTHTOKEN")
}

getFILE(){
	echo "Downloading $2"
	curl -sL $1 \
		-H "Accept: application/octet-stream" \
    -H "Authorization: token $AUTHTOKEN" \
    -o "$2"
}

URL=$(baseURL $USERNAME $REPOSITORY)

latestURL="$URL/releases/latest"

echo "Updating $USERNAME/$REPOSITORY"

latest=$(getJSON "$latestURL")
assetURL=$(echo $latest | jq -r '.assets_url')
assets=$(echo $(getJSON "$assetURL") | jq '.[] | select( '$ASSETSSELECTOR' )')

assetsName=($(echo $assets | jq '.name'))
assetsUrl=($(echo $assets | jq '.url'))
assetsId=($(echo $assets | jq '.node_id'))
assetsSize=($(echo $assets | jq '.size'))
assetsLength="${#assetsId[@]}"

for (( i=0; i<$assetsLength; i++ ))
do 
	destination="${DESTINATIONDIR}/$(echo ${assetsName[$i]} | sed 's/\"//g')"

	download=true

	if [ -f "$destination" ]
	then
	  currentSize=$(stat --printf="%s" $destination)
		if [ $currentSize == $(echo ${assetsSize[$i]} | sed 's/\"//g') ]
		then
			download=false
		else
			download=true
		fi

		if [ -f "${DESTINATIONDIR}/.node_id_$(echo ${assetsId[$i]} | sed 's/\"//g')" ]
		then
	    download=false
	  else
	  	download=true
		fi
	fi

	if [ $download == true ]
	then
	  getFILE "$(echo ${assetsUrl[$i]} | sed 's/\"//g')" $destination
	  echo $(date) > "${DESTINATIONDIR}/.node_id_$(echo ${assetsId[$i]} | sed 's/\"//g')"
	else
		echo "Skipping $destination (already latest)"
	fi
done
