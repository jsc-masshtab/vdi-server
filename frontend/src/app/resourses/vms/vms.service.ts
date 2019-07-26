import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public getAllVms(id?:string): QueryRef<any,any> {
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