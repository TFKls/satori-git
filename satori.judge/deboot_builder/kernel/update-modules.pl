#!/usr/bin/perl
use strict;
use File::Copy;
use Data::Dumper;

my $dir=$ARGV[0];
my $src=$ARGV[1];

my $modules = {};
my $source = {};

die "No kernel" unless -d "$dir/initrd/lib/modules";
open M, "find $dir/initrd/lib/modules -type f |";
while(<M>)
{
  chomp;
  my $file = $_;
  $modules->{$1} = $file if($file =~ m/.*?([^\/]+)$/);
}
close M;

die "No source" unless -d $src;
open M, "find $src -type f |";
while(<M>)
{
  chomp;
  my $file = $_;
  $source->{$1} = $file if($file =~ m/.*?([^\/]+)$/);
}
close M;

foreach my $m (keys %$modules)
{
  print "--- !!! --- ### --- !!! --- Module $m not found\n" unless defined $source->{$m};
}

foreach my $m (keys %$modules)
{
  if(defined $source->{$m})
  {
#    print "Module $m is ok!\n";
    copy($source->{$m},$modules->{$m});
  }
  else
  {
  	unlink $modules->{$m};
  }
}
