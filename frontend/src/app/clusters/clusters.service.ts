import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class ClustersService  {

    constructor(private service: Apollo) {}

    public getAllTeplates(): QueryRef<any,any> {
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

}
