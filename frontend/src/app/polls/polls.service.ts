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
                                    initial_size
                                    reserve_size
                                    state {
                                        running
                                        pending
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
                                    name
                                }  
                            }
                         
             
                     `,
            variables: {
                method: 'GET'
            }
        }) 
    }
}
