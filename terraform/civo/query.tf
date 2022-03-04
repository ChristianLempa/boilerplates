# CIVO Queries
# ---
# Query commonly used cloud resources from CIVO API

# CIVO Instance Sizes 
data "civo_size" "instance_xsmall" {
    filter {
        key = "name"
        values = ["g3.xsmall"]
        match_by = "re"
    }
}

data "civo_size" "instance_small" {
    filter {
        key = "name"
        values = ["g3.small"]
        match_by = "re"
    }
}

data "civo_size" "instance_medium" {
    filter {
        key = "name"
        values = ["g3.medium"]
        match_by = "re"
    }
}

data "civo_size" "instance_large" {
    filter {
        key = "name"
        values = ["g3.large"]
        match_by = "re"
    }
}

data "civo_size" "instance_xlarge" {
    filter {
        key = "name"
        values = ["g3.xlarge"]
        match_by = "re"
    }
}

data "civo_size" "instance_2xlarge" {
    filter {
        key = "name"
        values = ["g3.2xlarge"]
        match_by = "re"
    }
}


# CIVO Kubernetes Standard Sizes
data "civo_size" "k8s_std_xsmall" {
    filter {
        key = "name"
        values = ["g3.k3s.xsmall"]
        match_by = "re"
    }
}

data "civo_size" "k8s_std_small" {
    filter {
        key = "name"
        values = ["g3.k3s.small"]
        match_by = "re"
    }
}

data "civo_size" "k8s_std_medium" {
    filter {
        key = "name"
        values = ["g3.k3s.medium"]
        match_by = "re"
    }
}

data "civo_size" "k8s_std_large" {
    filter {
        key = "name"
        values = ["g3.k3s.large"]
        match_by = "re"
    }
}

data "civo_size" "k8s_std_xlarge" {
    filter {
        key = "name"
        values = ["g3.k3s.xlarge"]
        match_by = "re"
    }
}

data "civo_size" "k8s_std_2xlarge" {
    filter {
        key = "name"
        values = ["g3.k3s.2xlarge"]
        match_by = "re"
    }
}


# CIVO Instance Diskimages
data "civo_disk_image" "debian" {
   filter {
        key = "name"
        values = ["debian-10"]
   }
}

data "civo_disk_image" "debian_9" {
   filter {
        key = "name"
        values = ["debian-9"]
   }
}

data "civo_disk_image" "ubuntu" {
   filter {
        key = "name"
        values = ["ubuntu-focal"]
   }
}

data "civo_disk_image" "ubuntu_bionic" {
   filter {
        key = "name"
        values = ["ubuntu-bionic"]
   }
}

data "civo_disk_image" "centos" {
   filter {
        key = "name"
        values = ["centos-7"]
   }
}
