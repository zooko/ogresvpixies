writem ()
{
    dest=$1;
    shift;
    echo $dest: $*;
    echo -e "\n\n$*\n\n" | write $dest
}
