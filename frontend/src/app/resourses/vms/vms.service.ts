import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public getAllVms(id?:string): QueryRef<any,any> {
        return  this.service.watchQuery({
            query:  gql` query vms {
                                    vms {
                                       name
                                       node { verbose_name }
                                       template { name }
                                    }  
                                }
                    `,
            variables: {
                method: 'GET'
            }
        }) 
    }
}