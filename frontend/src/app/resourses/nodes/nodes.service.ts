import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class NodesService {

    constructor(private service: Apollo) {}

    public getAllNodes(cluster_id?:string): QueryRef<any,any> {

        return  this.service.watchQuery({
            query:  gql` query allNodes($cluster_id: String) {
                            controllers {
                                nodes(cluster_id: $cluster_id) {
                                    id
                                    verbose_name
                                    status
                                    datacenter_id
                                    datacenter_name
                                    cpu_count
                                    memory_count
                                    management_ip
                                    cluster {
                                        verbose_name
                                        id
                                    }
                                }
                            }
                           
                        }
            
                    `,
            variables: {
                method: 'GET',
                cluster_id: cluster_id
            }
        }) 
    }

    public getNode(node_id:string): QueryRef<any,any> {
        
        return  this.service.watchQuery({
            query:  gql` query node($id: String) {
                            node(id: $id) {
                                verbose_name
                                status
                                cpu_count
                                memory_count
                                management_ip
                                cluster {
                                    verbose_name
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
                id: node_id
            }
        }) 
    }

}
