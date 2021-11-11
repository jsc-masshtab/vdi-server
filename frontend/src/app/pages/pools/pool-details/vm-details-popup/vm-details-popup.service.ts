import { Injectable } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class VmDetailsPopupService {

  constructor(private service: Apollo) { }

  public convertToTemplate(vm_id: string, data) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation pools($verbose_name: ShortString!, $vm_id: UUID!,$controller_id: UUID!) {
            convertToTemplate(verbose_name: $verbose_name, vm_id: $vm_id, controller_id: $controller_id){
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        vm_id,
        ...data
      }
    });
  }
}
