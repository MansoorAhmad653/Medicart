"""
Management command to initialize Supabase storage bucket for medicine images
"""
import os
from django.core.management.base import BaseCommand
from supabase import create_client


class Command(BaseCommand):
    help = 'Initialize Supabase storage bucket for medicine images'
    
    def handle(self, *args, **options):
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                self.stdout.write(
                    self.style.ERROR('❌ SUPABASE_URL or SUPABASE_KEY not set in .env')
                )
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Check if bucket exists
            try:
                buckets = supabase.storage.list_buckets()
                bucket_names = [b.name for b in buckets]
                
                if 'medicines' in bucket_names:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Bucket "medicines" already exists')
                    )
                else:
                    # Create bucket
                    supabase.storage.create_bucket(
                        'medicines',
                        options={
                            'public': True
                        }
                    )
                    self.stdout.write(
                        self.style.SUCCESS('✅ Created bucket "medicines" in Supabase')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Could not verify bucket: {str(e)}')
                )
                self.stdout.write(
                    self.style.WARNING('Please manually create a public bucket named "medicines" in Supabase Dashboard')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
