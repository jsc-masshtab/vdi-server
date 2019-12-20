import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public getAllVms(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms {
                                vms {
                                    verbose_name
                                    controller { address }
                                    template { verbose_name }
                                    state
                                    status
                                    id
                                }
                            }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getVm(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms($id: String, $controller_address: String) {
                            vm(id: $id, controller_address: $controller_address) {
                                verbose_name
                                controller { address }
                                template { verbose_name }
                                state
                                user {
                                    username
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}
