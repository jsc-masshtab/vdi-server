import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class ClustersService  {

    constructor(private service: Apollo) {}

    public getAllClusters(): QueryRef<any,any> {
        let controller_ip = JSON.parse(localStorage.getItem('controller'));
        return  this.service.watchQuery({
            query:  gql` query allClusters($controller_ip: String) {
                            clusters(controller_ip: $controller_ip) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                            }
                        }
            
                    `,
            variables: {
                method: 'GET',
                controller_ip: controller_ip
            }
        }) 
    }

    public getCluster(id:string): QueryRef<any,any> {
        return  this.service.watchQuery({
            query:  gql` query cluster($id: String) {
                            cluster(id: $id) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                                nodes {
                                    verbose_name
                                    status
                                    cpu_count
                                    memory_count
                                    management_ip
                                }
                                datapools {
                                    used_space
                                    free_space
                                    size
                                    status
                                    type
                                    vdisk_count
                                    file_count
                                    iso_count
                                    verbose_name
                                }
                                templates {
                                    info
                                }
                                vms {
                                    name
                                    template {
                                        name 
                                    }
                                    node { 
                                        verbose_name
                                    }
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id: id
            }
        }) 
    }

}