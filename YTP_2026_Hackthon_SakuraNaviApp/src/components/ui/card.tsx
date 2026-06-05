import { memo } from "react";
import { Text, TextClassContext } from '@/components/ui/text';
import { cn } from '@/lib/utils';
import { View } from 'react-native';

const Card = memo(function Card({ className, ...props }: React.ComponentProps<typeof View>) {
  return (
    <TextClassContext.Provider value="text-card-foreground">
      <View
        className={cn(
          'bg-card border-border flex flex-col gap-6 rounded-xl border py-6 shadow-sm shadow-black/5',
          className
        )}
        {...props}
      />
    </TextClassContext.Provider>
  );
});

const CardHeader = memo(function CardHeader({ className, ...props }: React.ComponentProps<typeof View>) {
  return <View className={cn('flex flex-col gap-1.5 px-6', className)} {...props} />;
});

const CardTitle = memo(function CardTitle({
  className,
  ...props
}: React.ComponentProps<typeof Text>) {
  return (
    <Text
      role="heading"
      aria-level={3}
      className={cn('font-semibold leading-none', className)}
      {...props}
    />
  );
});

const CardDescription = memo(function CardDescription({
  className,
  ...props
}: React.ComponentProps<typeof Text>) {
  return <Text className={cn('text-muted-foreground text-sm', className)} {...props} />;
});

const CardContent = memo(function CardContent({ className, ...props }: React.ComponentProps<typeof View>) {
  return <View className={cn('px-6', className)} {...props} />;
});

const CardFooter = memo(function CardFooter({ className, ...props }: React.ComponentProps<typeof View>) {
  return <View className={cn('flex flex-row items-center px-6', className)} {...props} />;
});

export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle };
