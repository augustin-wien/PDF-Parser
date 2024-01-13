#!/bin/bash

BASE_URL="http://localhost:10014"
source .env

# Get the list of post IDs
smallest_id=0
highest_id=0
post_id=$(curl -X GET $BASE_URL/wp-json/wp/v2/posts?per_page=100  | jq '.[].id')
if (( $post_id < $smallest_id )); then
    echo "Smallest ID: $smallest_id vs. $post_id"
    smallest_id=$post_id
fi

if (( $post_id > $highest_id )); then
    echo "Highest ID: $highest_id vs. $post_id"
    highest_id=$post_id
fi
# Find the smallest and highest numbers
# smallest_id=$(echo "$post_ids" | jq 'min')
# highest_id=$(echo "$post_ids" | jq 'max')

# echo "Smallest ID: $smallest_id"
# echo "Highest ID: $highest_id"
echo "Post IDs: $post_ids"


# Function to delete a post by ID
delete_post() {
    local POST_ID=$1
    local DELETE_URL="$BASE_URL/wp-json/wp/v2/posts/$POST_ID"
    echo "Deleting post with ID: $POST_ID"
    curl --user "$WP_API_USER:$WP_API_KEY" -X DELETE $DELETE_URL
}

# Iterate through post IDs and delete posts
# for ((id=710; id<=850; id++)); do
#     delete_post $id
# done

# echo "$WP_API_USER:$WP_API_KEY"

# Sample curl command to delete a single post
# curl --user "admin:iTef fMhJ Rcij Azj3 Uban KGrw" -X DELETE http://localhost:10014/wp-json/wp/v2/posts/111

# curl -X GET http://localhost:10014/wp-json/wp/v2/posts?per_page=100 | jq '.[].id'