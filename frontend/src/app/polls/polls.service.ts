import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class PoolsService  {

    constructor(private service: Apollo) {}

    public getAllPools(): QueryRef<any,any> {
        console.log('piy');
       return  this.service.watchQuery({
            query:  gql` query allPools {
                                pools {
                                    id
                                    template_id
                                    name
                                    initial_size
                                    reserve_size
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

    public getAllPoolsCache() {
        return  this.service.getClient().readQuery({
            query:  gql` query allPools {
                                pools {
                                    id
                                    template_id
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
                                    name
                                }  
                            }
                         
             
                     `,
            variables: {
                method: 'GET'
            }
        }) 
    }

    public createPoll(name:string,id:string) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddPool($name: String!,$id: String!) {
                                addPool(name: $name, template_id: $id) {
                                    id
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id: id,
                name: name
            }
        })
    }
}
