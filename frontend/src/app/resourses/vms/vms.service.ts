import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public getAllVms(cluster_id?:string,node_id?:string,datapool_id?:string): QueryRef<any,any> {

        if(cluster_id) {
            return  this.service.watchQuery({
                query:  gql` query list_free_vms($cluster_id: String,$node_id:String,$datapool_id:String) {
                                        list_of_vms(cluster_id: $cluster_id,node_id:$node_id,datapool_id:$datapool_id) {
                                            id
                                            name
                                        }
                                    }
                        `,
                variables: {
                    method: 'GET',
                    cluster_id:cluster_id,
                    node_id: node_id,
                    datapool_id: datapool_id,
                    get_vms_in_pools: false
                }
            })
        } else {
            return  this.service.watchQuery({
                query:  gql` query vms {
                                        controllers {
                                            vms {
                                                name
                                                node { verbose_name }
                                                template { name }
                                                state
                                            }  
                                        }
                                    }
                        `,
                variables: {
                    method: 'GET'
                }
            }) 
        }
   
    }
}