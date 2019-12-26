import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class TemplatesService {

    constructor(private service: Apollo) {}

    public getAllTemplates(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms {
                                templates {
                                    veil_info_json
                                    controller {
                                        address
                                    }
                                }
                            }
                        `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getTemplate(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms($id: String, $controller_address: String) {
                            template(id: $id, controller_address: $controller_address) {
                                veil_info_json
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
