import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class PoolsService  {

    constructor(private service: Apollo) {}

    public getAllPools(): QueryRef<any,any> {
       return  this.service.watchQuery({
            query:  gql` query allPools {
                                pools {
                                    id
                                    template_id
                                    name
                                    settings {
                                        initial_size
                                        reserve_size
                                    }
                                    state {
                                        running
                                        pending
                                        available {
                                            name
                                            id
                                            info
                                        }
                                      }
                                }  
                            }
                        
            
                    `,
            variables: {
                method: 'GET'
            }
        }) 
    }

    public getAllTemplates(): QueryRef<any,any> {
        return  this.service.watchQuery({
            query:  gql` query allTemplates {
                                templates {
                                    id
                                    info
                                }  
                            }
                         
             
                     `,
            variables: {
                method: 'GET'
            }
        }) 
    }

    public createPoll(name: string,template_id: string,cluster_id: string,node_id: string,datapool_id: string,initial_size: number,reserve_size: number) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddPool($name: String!,$template_id: String,$cluster_id: String,$node_id: String,$datapool_id: String,$initial_size: Int,$reserve_size: Int) {
                                addPool(name: $name, template_id: $template_id,cluster_id: $cluster_id,node_id: $node_id,datapool_id: $datapool_id,initial_size: $initial_size,reserve_size: $reserve_size) {
                                    id
                                }
                            }
            `,
            variables: {
                method: 'POST',
                name: name,
                template_id: template_id,
                cluster_id: cluster_id,
                node_id: node_id,
                datapool_id: datapool_id,
                initial_size: initial_size,
                reserve_size: reserve_size
            }
        })
    }
}
