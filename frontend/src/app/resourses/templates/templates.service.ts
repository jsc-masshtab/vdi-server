import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class TemplatesService {

    constructor(private service: Apollo) {}

    public getAllTemplates(id?:string): QueryRef<any,any> {
        return  this.service.watchQuery({
            query:  gql` query allTemplates {
                                controllers {
                                    templates {
                                        id
                                        info
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
